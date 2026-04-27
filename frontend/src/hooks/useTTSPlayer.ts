import { useRef, useCallback, useState } from 'react'

interface UseTTSPlayerOptions {
  onQueueEmpty?: () => void
}

export function useTTSPlayer({ onQueueEmpty }: UseTTSPlayerOptions = {}) {
  const [playing, setPlaying] = useState(false)
  const [queueSize, setQueueSize] = useState(0)
  const audioContextRef = useRef<AudioContext | null>(null)
  const queueRef = useRef<Array<{ data: string; format: string; sampleRate: number }>>([])
  const playingRef = useRef(false)

  const playNext = useCallback(() => {
    if (queueRef.current.length === 0) {
      playingRef.current = false
      setPlaying(false)
      setQueueSize(0)
      onQueueEmpty?.()
      return
    }

    playingRef.current = true
    const { data, format, sampleRate } = queueRef.current.shift()!
    setQueueSize(queueRef.current.length)

    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext()
    }
    const ctx = audioContextRef.current

    try {
      const binaryString = atob(data)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }

      // Backend sends raw PCM (pcm_s16le); decodeAudioData only handles encoded
      // audio (WAV/MP3/OGG). For pcm_s16le we must build the AudioBuffer manually.
      if (format === 'pcm_s16le' || format === 'pcm') {
        const int16 = new Int16Array(bytes.buffer)
        if (int16.length === 0) {
          playNext()
          return
        }
        const float32 = new Float32Array(int16.length)
        for (let i = 0; i < int16.length; i++) {
          float32[i] = int16[i] / 32768.0
        }
        const audioBuffer = ctx.createBuffer(1, float32.length, sampleRate)
        audioBuffer.copyToChannel(float32, 0)
        const source = ctx.createBufferSource()
        source.buffer = audioBuffer
        source.connect(ctx.destination)
        source.onended = () => playNext()
        source.start()
      } else {
        // For encoded formats (wav/mp3) use decodeAudioData
        ctx.decodeAudioData(bytes.buffer, (buffer) => {
          const source = ctx.createBufferSource()
          source.buffer = buffer
          source.connect(ctx.destination)
          source.onended = () => playNext()
          source.start()
        }, () => {
          playNext()
        })
      }
    } catch {
      playNext()
    }
  }, [onQueueEmpty])

  const enqueueBase64 = useCallback((data: string, format: string, sampleRate: number) => {
    queueRef.current.push({ data, format, sampleRate })
    setQueueSize(queueRef.current.length)
    if (!playingRef.current) {
      setPlaying(true)
      playNext()
    }
  }, [playNext])

  const clear = useCallback(() => {
    queueRef.current = []
    setQueueSize(0)
    setPlaying(false)
    playingRef.current = false
  }, [])

  return { playing, queueSize, enqueueBase64, clear }
}
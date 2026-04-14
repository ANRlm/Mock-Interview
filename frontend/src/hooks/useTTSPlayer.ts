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
    const { data } = queueRef.current.shift()!
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

      ctx.decodeAudioData(bytes.buffer, (buffer) => {
        const source = ctx.createBufferSource()
        source.buffer = buffer
        source.connect(ctx.destination)
        source.onended = () => {
          playNext()
        }
        source.start()
      }, () => {
        playNext()
      })
    } catch {
      playNext()
    }
  }, [onQueueEmpty])

  const enqueueBase64 = useCallback((data: string, format: string, _sampleRate: number) => {
    queueRef.current.push({ data, format, sampleRate: _sampleRate })
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
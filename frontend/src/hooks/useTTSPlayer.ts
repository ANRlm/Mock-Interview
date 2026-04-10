import { useCallback, useEffect, useRef, useState } from 'react'

interface QueueItem {
  audioBytes: ArrayBuffer
  format: 'wav' | 'mp3'
}

const CROSSFADE_MS = 20

interface UseTTSPlayerResult {
  playing: boolean
  queueSize: number
  enqueueBase64: (base64Audio: string, format: 'wav' | 'mp3') => void
  clear: () => void
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = window.atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes.buffer
}

export function useTTSPlayer(onQueueFinished?: () => void): UseTTSPlayerResult {
  const queueRef = useRef<QueueItem[]>([])
  const currentUrlRef = useRef<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const playingRef = useRef(false)
  const onQueueFinishedRef = useRef(onQueueFinished)
  const [playing, setPlaying] = useState(false)
  const [queueSize, setQueueSize] = useState(0)

  useEffect(() => {
    onQueueFinishedRef.current = onQueueFinished
  }, [onQueueFinished])

  const playNextRef = useRef<() => void>(() => undefined)
  const audioContextRef = useRef<AudioContext | null>(null)
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null)
  const gainNodeRef = useRef<GainNode | null>(null)
  const decodeChainRef = useRef(Promise.resolve())

  const clear = useCallback(() => {
    queueRef.current = []
    setQueueSize(0)
    playingRef.current = false
    setPlaying(false)

    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.removeAttribute('src')
      audioRef.current.load()
    }
    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.stop()
      } catch {
        // ignore
      }
      sourceNodeRef.current.disconnect()
      sourceNodeRef.current = null
    }
    if (gainNodeRef.current) {
      gainNodeRef.current.disconnect()
      gainNodeRef.current = null
    }
    if (currentUrlRef.current) {
      URL.revokeObjectURL(currentUrlRef.current)
      currentUrlRef.current = null
    }
  }, [])

  const enqueueBase64 = useCallback((base64Audio: string, format: 'wav' | 'mp3') => {
    queueRef.current.push({
      audioBytes: base64ToArrayBuffer(base64Audio),
      format,
    })
    setQueueSize(queueRef.current.length)

    if (!playingRef.current) {
      playNextRef.current()
    }
  }, [])

  useEffect(() => {
    const playNext = () => {
      const next = queueRef.current.shift()
      setQueueSize(queueRef.current.length)
      if (!next) {
        playingRef.current = false
        setPlaying(false)
        onQueueFinishedRef.current?.()
        return
      }

      playingRef.current = true
      setPlaying(true)

      decodeChainRef.current = decodeChainRef.current
        .catch(() => undefined)
        .then(async () => {
          let ctx = audioContextRef.current
          if (!ctx) {
            ctx = new AudioContext({ latencyHint: 'interactive' })
            audioContextRef.current = ctx
          }
          if (ctx.state === 'suspended') {
            await ctx.resume()
          }

          const decoded = await ctx.decodeAudioData(next.audioBytes.slice(0))
          const source = ctx.createBufferSource()
          source.buffer = decoded

          const gain = ctx.createGain()
          gain.gain.setValueAtTime(0.0001, ctx.currentTime)
          gain.gain.linearRampToValueAtTime(1.0, ctx.currentTime + CROSSFADE_MS / 1000)

          source.connect(gain)
          gain.connect(ctx.destination)

          source.onended = () => {
            if (sourceNodeRef.current === source) {
              sourceNodeRef.current = null
            }
            gain.disconnect()
            window.setTimeout(() => {
              playNextRef.current()
            }, 0)
          }

          sourceNodeRef.current = source
          gainNodeRef.current = gain
          source.start()
        })
        .catch(() => {
          playingRef.current = false
          setPlaying(false)
          window.setTimeout(() => {
            playNextRef.current()
          }, 0)
        })
    }

    playNextRef.current = playNext

    return () => {
      // noop
    }
  }, [])

  useEffect(() => {
    return () => {
      clear()
      if (audioContextRef.current) {
        void audioContextRef.current.close()
        audioContextRef.current = null
      }
    }
  }, [clear])

  return {
    playing,
    queueSize,
    enqueueBase64,
    clear,
  }
}

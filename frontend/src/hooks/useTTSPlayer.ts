import { useCallback, useEffect, useRef, useState } from 'react'

interface QueueItem {
  audioBytes: ArrayBuffer
  format: 'wav' | 'mp3' | 'pcm_s16le'
  sampleRate: number
}

interface UseTTSPlayerResult {
  playing: boolean
  queueSize: number
  enqueueBase64: (base64Audio: string, format: 'wav' | 'mp3' | 'pcm_s16le', sampleRate?: number) => void
  clear: () => void
}

const CROSSFADE_MS = 16
const PREFETCH_MIN_QUEUE = 1
const DEFAULT_SAMPLE_RATE = 22050

function pcm16ToAudioBuffer(ctx: AudioContext, pcmBytes: ArrayBuffer, sampleRate: number): AudioBuffer {
  const source = new Int16Array(pcmBytes)
  const frames = source.length
  const buffer = ctx.createBuffer(1, Math.max(1, frames), sampleRate)
  const channel = buffer.getChannelData(0)
  for (let i = 0; i < frames; i += 1) {
    channel[i] = source[i] / 32768
  }
  return buffer
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
  const onQueueFinishedRef = useRef(onQueueFinished)
  const [playing, setPlaying] = useState(false)
  const [queueSize, setQueueSize] = useState(0)

  const audioContextRef = useRef<AudioContext | null>(null)
  const activeNodeRef = useRef<AudioBufferSourceNode | null>(null)
  const activeGainRef = useRef<GainNode | null>(null)
  const decodeChainRef = useRef(Promise.resolve())
  const playingRef = useRef(false)

  useEffect(() => {
    onQueueFinishedRef.current = onQueueFinished
  }, [onQueueFinished])

  const ensureAudioContext = useCallback(async () => {
    let ctx = audioContextRef.current
    if (!ctx) {
      ctx = new AudioContext({ latencyHint: 'interactive' })
      audioContextRef.current = ctx
    }
    if (ctx.state === 'suspended') {
      await ctx.resume()
    }
    return ctx
  }, [])

  const stopCurrentNode = useCallback(() => {
    if (activeNodeRef.current) {
      try {
        activeNodeRef.current.stop()
      } catch {
        // noop
      }
      activeNodeRef.current.disconnect()
      activeNodeRef.current = null
    }
    if (activeGainRef.current) {
      activeGainRef.current.disconnect()
      activeGainRef.current = null
    }
  }, [])

  const clear = useCallback(() => {
    queueRef.current = []
    setQueueSize(0)
    playingRef.current = false
    setPlaying(false)
    stopCurrentNode()
  }, [stopCurrentNode])

  const playNextRef = useRef<() => void>(() => undefined)

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
          const ctx = await ensureAudioContext()
          const decoded =
            next.format === 'pcm_s16le'
              ? pcm16ToAudioBuffer(ctx, next.audioBytes, next.sampleRate)
              : await ctx.decodeAudioData(next.audioBytes.slice(0))

          stopCurrentNode()

          const source = ctx.createBufferSource()
          source.buffer = decoded
          const gain = ctx.createGain()
          gain.gain.setValueAtTime(0.0001, ctx.currentTime)
          gain.gain.linearRampToValueAtTime(1.0, ctx.currentTime + CROSSFADE_MS / 1000)

          source.connect(gain)
          gain.connect(ctx.destination)

          source.onended = () => {
            if (activeNodeRef.current === source) {
              activeNodeRef.current = null
            }
            gain.disconnect()
            window.setTimeout(() => {
              playNextRef.current()
            }, 0)
          }

          activeNodeRef.current = source
          activeGainRef.current = gain
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
  }, [ensureAudioContext, stopCurrentNode])

  const enqueueBase64 = useCallback(
    (base64Audio: string, format: 'wav' | 'mp3' | 'pcm_s16le', sampleRate?: number) => {
      queueRef.current.push({
        audioBytes: base64ToArrayBuffer(base64Audio),
        format,
        sampleRate: sampleRate && sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE,
      })
      setQueueSize(queueRef.current.length)

      if (!playingRef.current && queueRef.current.length >= PREFETCH_MIN_QUEUE) {
        playNextRef.current()
      }
      if (!playingRef.current && queueRef.current.length > 0) {
        window.setTimeout(() => {
          if (!playingRef.current && queueRef.current.length > 0) {
            playNextRef.current()
          }
        }, 40)
      }
    },
    [],
  )

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

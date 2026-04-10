import { useCallback, useEffect, useRef, useState } from 'react'

interface QueueItem {
  audioBytes: ArrayBuffer
  format: 'wav' | 'mp3'
}

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

      const mime = next.format === 'mp3' ? 'audio/mpeg' : 'audio/wav'
      const blob = new Blob([next.audioBytes], { type: mime })
      const url = URL.createObjectURL(blob)

      if (!audioRef.current) {
        audioRef.current = new Audio()
      }
      const audio = audioRef.current

      if (currentUrlRef.current) {
        URL.revokeObjectURL(currentUrlRef.current)
        currentUrlRef.current = null
      }

      currentUrlRef.current = url
      audio.src = url
      playingRef.current = true
      setPlaying(true)

      void audio.play().catch(() => {
        playingRef.current = false
        setPlaying(false)
        window.setTimeout(() => {
          playNextRef.current()
        }, 0)
      })
    }

    playNextRef.current = playNext

    const audio = audioRef.current ?? new Audio()
    audioRef.current = audio
    const onEnded = () => {
      playNextRef.current()
    }
    audio.addEventListener('ended', onEnded)

    return () => {
      audio.removeEventListener('ended', onEnded)
    }
  }, [])

  useEffect(() => {
    return () => {
      clear()
    }
  }, [clear])

  return {
    playing,
    queueSize,
    enqueueBase64,
    clear,
  }
}

import { useState, useCallback, useRef } from 'react'
import { useAuthStore } from '@/stores/authStore'

export function useManualTTS() {
  const [status, setStatus] = useState<'idle' | 'playing'>('idle')
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const token = useAuthStore((s) => s.token)

  const play = useCallback(async (_messageId: string, text: string) => {
    setStatus('playing')
    try {
      const res = await fetch(`/api/tts/speak`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text }),
      })

      if (res.ok) {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audioRef.current = audio

        audio.onended = () => {
          setStatus('idle')
          URL.revokeObjectURL(url)
        }

        audio.onerror = () => {
          setStatus('idle')
          URL.revokeObjectURL(url)
        }

        await audio.play()
      } else {
        setStatus('idle')
      }
    } catch {
      setStatus('idle')
    }
  }, [token])

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    setStatus('idle')
  }, [])

  return { status, play, stop }
}
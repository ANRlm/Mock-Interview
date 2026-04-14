import { useCallback, useRef, useState } from 'react'

import { useAuthStore } from '@/stores/authStore'

export type ManualTtsStatus = 'idle' | 'connecting' | 'playing' | 'error'

interface PendingAudio {
  id: string
  audioBytes: ArrayBuffer
  format: 'wav' | 'mp3' | 'pcm_s16le'
  sampleRate: number
}

interface UseManualTTSResult {
  status: ManualTtsStatus
  play: (messageId: string, text: string) => void
  stop: () => void
}

const CROSSFADE_MS = 16
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

export function useManualTTS(): UseManualTTSResult {
  const [status, setStatus] = useState<ManualTtsStatus>('idle')
  const token = useAuthStore((s) => s.token)
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const activeNodeRef = useRef<AudioBufferSourceNode | null>(null)
  const activeGainRef = useRef<GainNode | null>(null)
  const currentMessageIdRef = useRef<string | null>(null)

  const stop = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    if (activeNodeRef.current) {
      try {
        activeNodeRef.current.stop()
      } catch {}
      activeNodeRef.current.disconnect()
      activeNodeRef.current = null
    }
    if (activeGainRef.current) {
      activeGainRef.current.disconnect()
      activeGainRef.current = null
    }
    currentMessageIdRef.current = null
    setStatus('idle')
  }, [])

  const play = useCallback((messageId: string, text: string) => {
    if (!token) return
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setStatus('connecting')
    currentMessageIdRef.current = messageId

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const sessionId = messageId
    const ws = new WebSocket(`${protocol}//${host}/ws/tts/${sessionId}?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('playing')
      ws.send(JSON.stringify({
        type: 'text_input',
        text,
        response_id: messageId,
      }))
    }

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'tts_audio') {
          const audioBytes = base64ToArrayBuffer(data.data)
          const format = data.format || 'pcm_s16le'
          const sampleRate = data.sample_rate || DEFAULT_SAMPLE_RATE

          let ctx = audioContextRef.current
          if (!ctx) {
            ctx = new AudioContext({ latencyHint: 'interactive' })
            audioContextRef.current = ctx
          }
          if (ctx.state === 'suspended') {
            await ctx.resume()
          }

          const decoded = format === 'pcm_s16le'
            ? pcm16ToAudioBuffer(ctx, audioBytes, sampleRate)
            : await ctx.decodeAudioData(audioBytes.slice(0))

          if (activeNodeRef.current) {
            try {
              activeNodeRef.current.stop()
            } catch {}
            activeNodeRef.current.disconnect()
          }

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
          }

          activeNodeRef.current = source
          activeGainRef.current = gain
          source.start()
        } else if (data.type === 'tts_done') {
          setStatus('idle')
          ws.close()
          wsRef.current = null
        }
      } catch {}
    }

    ws.onerror = () => {
      setStatus('error')
    }

    ws.onclose = () => {
      if (status === 'playing') {
        setStatus('idle')
      }
      wsRef.current = null
    }
  }, [token, status])

  return { status, play, stop }
}

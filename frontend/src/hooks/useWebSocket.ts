import { useEffect, useRef, useCallback } from 'react'
import { useAuthStore } from '@/stores/authStore'

interface UseWebSocketOptions {
  sessionId: string
  onMessage: (payload: Record<string, unknown>) => void
}

export function useWebSocket({ sessionId, onMessage }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const token = useAuthStore((s) => s.token)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/interview/${sessionId}?token=${token}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      reconnectAttemptsRef.current = 0
      startPing()
    }

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'pong') return
        onMessage(payload)
      } catch {
      }
    }

    ws.onclose = () => {
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          reconnectAttemptsRef.current++
          connect()
        }, 1000 * Math.min(30, 2 ** reconnectAttemptsRef.current))
      }
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [sessionId, token, onMessage])

  const startPing = useCallback(() => {
    const ping = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
      setTimeout(ping, 30000)
    }
    ping()
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  const sendAudioChunk = useCallback((chunk: ArrayBuffer, sampleRate: number) => {
    const base64 = btoa(String.fromCharCode(...new Uint8Array(chunk)))
    send({ type: 'audio_chunk', data: base64, sample_rate: sampleRate })
  }, [send])

  const sendAudioEnd = useCallback(() => {
    send({ type: 'audio_end' })
  }, [send])

  const sendInterrupt = useCallback((reason: string) => {
    send({ type: 'interrupt', reason })
  }, [send])

  const connected = wsRef.current?.readyState === WebSocket.OPEN

  return { send, sendAudioChunk, sendAudioEnd, sendInterrupt, connected }
}
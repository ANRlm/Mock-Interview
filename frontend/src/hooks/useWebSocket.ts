import { useEffect, useRef, useCallback, useState } from 'react'
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
  const [connected, setConnected] = useState(false)

  const connect = useCallback(() => {
    if (!token) return

    const wsUrl = `/ws/interview/${sessionId}?token=${token}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      reconnectAttemptsRef.current = 0
      setConnected(true)
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
      setConnected(false)
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
      return true
    }
    return false
  }, [])

  const sendAudioChunk = useCallback((chunk: ArrayBuffer, sampleRate: number) => {
    const base64 = btoa(String.fromCharCode(...new Uint8Array(chunk)))
    return send({ type: 'audio_chunk', data: base64, sample_rate: sampleRate })
  }, [send])

  const sendAudioEnd = useCallback(() => {
    return send({ type: 'audio_end' })
  }, [send])

  const sendInterrupt = useCallback((reason: string) => {
    return send({ type: 'interrupt', reason })
  }, [send])

  return { send, sendAudioChunk, sendAudioEnd, sendInterrupt, connected }
}
import { useEffect, useRef, useCallback, useState } from 'react'
import { useAuthStore } from '@/stores/authStore'

interface UseWebSocketOptions {
  sessionId: string
  onMessage: (payload: Record<string, unknown>) => void
}

export function useWebSocket({ sessionId, onMessage }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const pingTimeoutRef = useRef<number | null>(null)
  const token = useAuthStore((s) => s.token)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5
  const disconnectDebounceRef = useRef<number | null>(null)

  const [connected, setConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)

  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!token) return

    const wsUrl = `/ws/interview/${sessionId}?token=${token}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    setIsConnecting(true)

    ws.onopen = () => {
      reconnectAttemptsRef.current = 0
      setConnected(true)
      setIsConnecting(false)
      startPing()
    }

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'pong') return
        onMessageRef.current(payload)
      } catch {
      }
    }

    ws.onclose = () => {
      if (disconnectDebounceRef.current) {
        clearTimeout(disconnectDebounceRef.current)
      }
      disconnectDebounceRef.current = window.setTimeout(() => {
        setConnected(false)
        setIsConnecting(false)

        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectAttemptsRef.current++
            connect()
          }, 1000 * Math.min(30, 2 ** reconnectAttemptsRef.current))
        }
      }, 500)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [sessionId, token])

  const startPing = useCallback(() => {
    if (pingTimeoutRef.current) {
      clearTimeout(pingTimeoutRef.current)
    }

    const ping = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
      pingTimeoutRef.current = window.setTimeout(ping, 30000)
    }
    ping()
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (pingTimeoutRef.current) {
        clearTimeout(pingTimeoutRef.current)
      }
      if (disconnectDebounceRef.current) {
        clearTimeout(disconnectDebounceRef.current)
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
    // btoa(String.fromCharCode(...new Uint8Array(chunk))) overflows the JS call
    // stack for large audio buffers. Use a chunked approach instead.
    const bytes = new Uint8Array(chunk)
    let binary = ''
    const CHUNK = 8192
    for (let i = 0; i < bytes.length; i += CHUNK) {
      binary += String.fromCharCode(...bytes.subarray(i, i + CHUNK))
    }
    const base64 = btoa(binary)
    return send({ type: 'audio_chunk', data: base64, sample_rate: sampleRate })
  }, [send])

  const sendAudioEnd = useCallback(() => {
    return send({ type: 'audio_end' })
  }, [send])

  const sendInterrupt = useCallback((reason: string) => {
    return send({ type: 'interrupt', reason })
  }, [send])

  return { send, sendAudioChunk, sendAudioEnd, sendInterrupt, connected, isConnecting }
}
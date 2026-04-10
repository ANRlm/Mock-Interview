import { useCallback, useEffect, useRef, useState } from 'react'

import { createInterviewSocket } from '@/services/websocket'
import type { WsServerMessage } from '@/types/interview'

interface UseWebSocketParams {
  sessionId: string | null
  onMessage: (message: WsServerMessage) => void
}

interface UseWebSocketResult {
  sendCandidateMessage: (text: string) => void
  sendAudioChunk: (base64Pcm: string, sampleRate: number) => void
  sendAudioEnd: () => void
  sendInterrupt: (reason?: string) => void
  connected: boolean
  reconnectCount: number
}

const MAX_RETRIES = 5

export function useWebSocket({ sessionId, onMessage }: UseWebSocketParams): UseWebSocketResult {
  const [connected, setConnected] = useState(false)
  const [reconnectCount, setReconnectCount] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const onMessageRef = useRef(onMessage)

  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    if (!sessionId) {
      return
    }

    let cancelled = false
    retryRef.current = 0

    const connect = () => {
      if (cancelled) {
        return
      }

      const ws = createInterviewSocket(
        sessionId,
        (payload) => {
          onMessageRef.current(payload)
        },
        () => {
          setConnected(false)
          if (cancelled || retryRef.current >= MAX_RETRIES) {
            return
          }

          retryRef.current += 1
          setReconnectCount(retryRef.current)
          const backoff = Math.min(1000 * 2 ** (retryRef.current - 1), 8000)
          window.setTimeout(connect, backoff)
        },
      )

      ws.onopen = () => {
        retryRef.current = 0
        setReconnectCount(0)
        setConnected(true)
      }

      ws.onerror = () => {
        setConnected(false)
      }

      wsRef.current = ws
    }

    connect()

    return () => {
      cancelled = true
      retryRef.current = MAX_RETRIES
      wsRef.current?.close()
      wsRef.current = null
      setConnected(false)
    }
  }, [sessionId])

  const sendCandidateMessage = useCallback((text: string) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return
    }

    ws.send(
      JSON.stringify({
        type: 'candidate_message',
        text,
      }),
    )
  }, [])

  const sendAudioChunk = useCallback((base64Pcm: string, sampleRate: number) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return
    }

    ws.send(
      JSON.stringify({
        type: 'audio_chunk',
        data: base64Pcm,
        sample_rate: sampleRate,
      }),
    )
  }, [])

  const sendAudioEnd = useCallback(() => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return
    }

    ws.send(
      JSON.stringify({
        type: 'audio_end',
      }),
    )
  }, [])

  const sendInterrupt = useCallback((reason = 'client_interrupt') => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return
    }

    ws.send(
      JSON.stringify({
        type: 'interrupt',
        reason,
      }),
    )
  }, [])

  return { sendCandidateMessage, sendAudioChunk, sendAudioEnd, sendInterrupt, connected, reconnectCount }
}

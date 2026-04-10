import type { WsServerMessage } from '@/types/interview'

export type OnMessage = (message: WsServerMessage) => void
export type OnClose = () => void

export function createInterviewSocket(sessionId: string, onMessage: OnMessage, onClose: OnClose): WebSocket {
  const base = import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:8000/ws'
  const ws = new WebSocket(`${base}/interview/${sessionId}`)

  ws.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data as string) as WsServerMessage
      onMessage(parsed)
    } catch {
      // ignore invalid payload
    }
  }

  ws.onclose = () => {
    onClose()
  }

  return ws
}

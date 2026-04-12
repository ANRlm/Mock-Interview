import type { WsServerMessage } from '@/types/interview'

export type OnMessage = (message: WsServerMessage) => void
export type OnClose = () => void

export function createInterviewSocket(sessionId: string, onMessage: OnMessage, onClose: OnClose): WebSocket {
  const configuredBase = import.meta.env.VITE_WS_BASE_URL ?? '/ws'
  const base = resolveWsBase(configuredBase)
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

function resolveWsBase(base: string): string {
  if (base.startsWith('ws://') || base.startsWith('wss://')) {
    return base
  }

  const normalized = base.startsWith('/') ? base : `/${base}`
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}${normalized}`
}

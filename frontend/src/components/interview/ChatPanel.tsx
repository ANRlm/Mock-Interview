import { useEffect, useRef } from 'react'
import { Bot, User } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { ConversationMessage } from '@/types/interview'

interface ChatPanelProps {
  messages: ConversationMessage[]
  streamText: string
}

export function ChatPanel({ messages, streamText }: ChatPanelProps) {
  const tailRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    tailRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' })
  }, [messages, streamText])

  return (
    <Card className="flex h-[60vh] min-h-0 flex-col">
      <CardHeader>
        <CardTitle className="text-base">对话记录</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 space-y-3 overflow-y-auto pb-6">
        {messages.length === 0 ? (
          <p className="rounded-lg border border-dashed border-slate-700 p-4 text-center text-sm text-slate-500">开始语音回答，系统会实时识别并由 AI 面试官追问。</p>
        ) : (
          messages.map((message) => {
            const isCandidate = message.role === 'candidate'
            return (
              <div key={message.id} className={`flex items-start gap-2 ${isCandidate ? 'justify-end' : 'justify-start'}`}>
                {!isCandidate && <Bot size={16} className="mt-1 text-cyan-300" />}
                <div
                  className={`max-h-72 max-w-[88%] overflow-y-auto rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap [overflow-wrap:anywhere] ${
                    isCandidate
                      ? 'bg-blue-500/20 text-blue-100 ring-1 ring-blue-500/30'
                      : 'bg-slate-800/80 text-slate-100 ring-1 ring-slate-700'
                  }`}
                >
                  {message.content}
                </div>
                {isCandidate && <User size={16} className="mt-1 text-blue-300" />}
              </div>
            )
          })
        )}

        {streamText ? (
          <div className="flex items-start gap-2">
            <Bot size={16} className="mt-1 text-cyan-300" />
            <div className="max-h-72 max-w-[88%] overflow-y-auto rounded-2xl bg-slate-800/80 px-4 py-3 text-sm text-slate-100 whitespace-pre-wrap [overflow-wrap:anywhere] ring-1 ring-cyan-400/30">
              {streamText}
              <span className="ml-1 inline-block h-4 w-[2px] animate-pulse bg-cyan-300 align-middle" />
            </div>
          </div>
        ) : null}
        <div ref={tailRef} />
      </CardContent>
    </Card>
  )
}

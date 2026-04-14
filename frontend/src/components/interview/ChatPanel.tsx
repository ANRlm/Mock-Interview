import { Volume2 } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { Bot, User } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MarkdownMessage } from '@/components/interview/MarkdownMessage'
import type { ConversationMessage } from '@/types/interview'

interface ChatPanelProps {
  messages: ConversationMessage[]
  streamText: string
  onReadAloud?: (messageId: string, text: string) => void
  ttsPlayingFor?: string | null
}

export function ChatPanel({ messages, streamText, onReadAloud, ttsPlayingFor }: ChatPanelProps) {
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
          <p className="rounded-lg border border-dashed border-neutral-700 p-4 text-center text-sm text-neutral-500">开始语音回答，系统会实时识别并由 AI 面试官追问。</p>
        ) : (
          messages.map((message) => {
            const isCandidate = message.role === 'candidate'
            const isPlaying = ttsPlayingFor === message.id
            return (
              <div key={message.id} className={`flex items-start gap-2 ${isCandidate ? 'justify-end' : 'justify-start'}`}>
                {!isCandidate && <Bot size={16} className="mt-1 text-neutral-400" />}
                <div className="group relative max-h-72 max-w-[88%] overflow-y-auto rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap [overflow-wrap:anywhere]">
                  <div className={`${isCandidate ? 'bg-neutral-800/80 text-neutral-100 ring-1 ring-neutral-600/50' : 'bg-neutral-800/80 text-neutral-100 ring-1 ring-neutral-700'}`}>
                    <MarkdownMessage content={message.content} />
                  </div>
                  {!isCandidate && onReadAloud && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="absolute top-1 right-1 h-7 px-2 text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => onReadAloud(message.id, message.content)}
                    >
                      <Volume2 size={14} className={isPlaying ? 'animate-pulse' : ''} />
                      <span className="ml-1 text-xs">{isPlaying ? '播放中' : '朗读'}</span>
                    </Button>
                  )}
                </div>
                {isCandidate && <User size={16} className="mt-1 text-neutral-400" />}
              </div>
            )
          })
        )}

        {streamText ? (
          <div className="flex items-start gap-2">
            <Bot size={16} className="mt-1 text-neutral-400" />
            <div className="max-h-72 max-w-[88%] overflow-y-auto rounded-2xl bg-neutral-800/80 px-4 py-3 text-sm text-neutral-100 whitespace-pre-wrap [overflow-wrap:anywhere] ring-1 ring-neutral-600/50">
              <MarkdownMessage content={streamText} streaming />
            </div>
          </div>
        ) : null}
        <div ref={tailRef} />
      </CardContent>
    </Card>
  )
}

import { useRef, useEffect } from 'react'
import { Play, Square } from 'lucide-react'
import { type Message } from '@/stores/interviewStore'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { AIVoiceAnimation } from './AIVoiceAnimation'

interface ChatPanelProps {
  messages: Message[]
  streamText: string
  onReadAloud?: (messageId: string, text: string) => void
  ttsPlayingFor?: string | null
  inputMode?: 'voice' | 'text'
  stage?: 'idle' | 'listening' | 'thinking' | 'speaking'
}

export function ChatPanel({ messages, streamText, onReadAloud, ttsPlayingFor, inputMode, stage }: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamText])

  return (
    <div className="flex flex-col rounded-xl border border-border dark:border-neutral-700 bg-surface dark:bg-neutral-900 min-h-[300px] max-h-[60vh] overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === 'candidate' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-xl px-4 py-3 ${
              message.role === 'candidate'
                ? 'bg-primary dark:bg-primary text-white'
                : 'bg-bg dark:bg-neutral-800 border border-border dark:border-neutral-700 text-text'
            }`}>
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
              <div className={`flex items-center justify-between mt-2 pt-2 gap-2 border-t ${
                message.role === 'candidate' ? 'border-white/20 flex-row-reverse' : 'border-border dark:border-neutral-700 flex-row'
              }`}>
                <span className="text-xs opacity-60">
                  第{message.turn_index}轮
                </span>
                {message.role === 'interviewer' && onReadAloud && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`h-6 px-1 text-xs ${ttsPlayingFor === message.id ? 'opacity-100' : 'opacity-60'}`}
                    onClick={() => onReadAloud(message.id, message.content)}
                  >
                    {ttsPlayingFor === message.id ? <Square size={12} /> : <Play size={12} />}
                    <span className="ml-1">朗读</span>
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
        {inputMode === 'voice' && (stage === 'thinking' || stage === 'speaking') ? (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-xl px-4 py-3 bg-bg dark:bg-neutral-800 border border-border dark:border-neutral-700 text-text">
              <AIVoiceAnimation stage={stage} />
            </div>
          </div>
        ) : streamText && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-xl px-4 py-3 bg-bg dark:bg-neutral-800 border border-border dark:border-neutral-700 text-text">
              <p className="text-sm whitespace-pre-wrap">{streamText}<span className="animate-pulse">▊</span></p>
              <Badge variant="default" className="mt-2">AI 回复中...</Badge>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
import { Mic, MicOff } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AudioPanelProps {
  level: number
  active: boolean
}

export function AudioPanel({ level, active }: AudioPanelProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-border dark:border-neutral-700 bg-surface dark:bg-neutral-900 p-6 h-[200px]">
      <div className={cn(
        'rounded-full p-6 transition-colors',
        active ? 'bg-primary/10 dark:bg-primary/20' : 'bg-surface dark:bg-neutral-800'
      )}>
        {active ? (
          <Mic size={48} className="text-primary animate-pulse" />
        ) : (
          <MicOff size={48} className="text-text-muted dark:text-neutral-500" />
        )}
      </div>
      <div className="mt-4 flex items-end gap-1 h-8">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className={cn(
              'w-1 rounded-full transition-all',
              active ? 'bg-primary dark:bg-primary' : 'bg-border dark:bg-neutral-700',
              active && `h-${Math.max(4, Math.min(32, level * 32 / 100 * (i + 1)))}`
            )}
            style={{
              height: active ? `${Math.max(4, Math.min(32, (level / 100) * 32 * ((i + 1) / 8)))}px` : '4px',
              opacity: active ? 0.4 + (i / 8) * 0.6 : 0.3,
            }}
          />
        ))}
      </div>
      <p className="mt-4 text-xs text-text-muted">
        {active ? '正在录音...' : '等待录音'}
      </p>
    </div>
  )
}
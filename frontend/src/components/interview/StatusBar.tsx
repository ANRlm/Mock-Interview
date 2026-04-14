import { Wifi, WifiOff, Mic, MicOff } from 'lucide-react'
import { type InterviewStage, type LLMStats } from '@/stores/interviewStore'
import { Badge } from '@/components/ui/Badge'

interface StatusBarProps {
  stage: InterviewStage
  connected: boolean
  turnCount: number
  sttPreview: string
  ttsQueueSize: number
  recording: boolean
  ttsProviderLabel: string
  llmStats: LLMStats | null
}

const stageLabels: Record<InterviewStage, string> = {
  idle: '等待开始',
  listening: '倾听中',
  thinking: '思考中',
  speaking: '回答中',
}

const stageColors: Record<InterviewStage, string> = {
  idle: 'default',
  listening: 'success',
  thinking: 'warning',
  speaking: 'error',
}

export function StatusBar({
  stage,
  connected,
  turnCount,
  sttPreview,
  ttsQueueSize,
  recording,
  ttsProviderLabel,
  llmStats,
}: StatusBarProps) {
  return (
    <div className="flex flex-col rounded-xl border border-border bg-surface p-4 h-[200px] space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">连接状态</span>
        {connected ? (
          <div className="flex items-center gap-1 text-green-600">
            <Wifi size={14} />
            <span className="text-xs">已连接</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-red-500">
            <WifiOff size={14} />
            <span className="text-xs">断开</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">当前阶段</span>
        <Badge variant={stageColors[stage] as 'default' | 'success' | 'warning' | 'error'}>
          {stageLabels[stage]}
        </Badge>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">已回答</span>
        <span className="text-sm font-medium text-text">{turnCount} 轮</span>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">麦克风</span>
        <div className="flex items-center gap-1">
          {recording ? <Mic size={14} className="text-red-500" /> : <MicOff size={14} className="text-text-muted" />}
          <span className="text-xs text-text">{recording ? '录音中' : '关闭'}</span>
        </div>
      </div>

      {sttPreview && (
        <div className="space-y-1">
          <span className="text-xs text-text-muted">识别预览</span>
          <p className="text-xs text-text bg-bg rounded px-2 py-1 truncate">{sttPreview}</p>
        </div>
      )}

      {ttsProviderLabel && (
        <div className="space-y-1">
          <span className="text-xs text-text-muted">TTS</span>
          <p className="text-xs text-text">{ttsProviderLabel} {ttsQueueSize > 0 && `(${ttsQueueSize} 队列)`}</p>
        </div>
      )}

      {llmStats && (
        <div className="space-y-1">
          <span className="text-xs text-text-muted">LLM 统计</span>
          <p className="text-xs text-text">
            {llmStats.tokens_per_second?.toFixed(1)} tok/s
          </p>
        </div>
      )}
    </div>
  )
}
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import type { InterviewStage, LlmTurnStats } from '@/types/interview'

interface StatusBarProps {
  stage: InterviewStage
  connected: boolean
  turnCount: number
  sttPreview: string
  ttsQueueSize: number
  recording: boolean
  ttsProviderLabel: string
  llmStats: LlmTurnStats | null
}

const stageTextMap: Record<InterviewStage, string> = {
  idle: '待机',
  listening: '聆听中',
  thinking: '思考中',
  speaking: '提问中',
}

const fmtSeconds = (value?: number) => {
  if (value === undefined) {
    return '-'
  }
  return `${value.toFixed(2)}s`
}

const fmtNumber = (value?: number) => {
  if (value === undefined) {
    return '-'
  }
  return value.toLocaleString()
}

const fmtTps = (value?: number) => {
  if (value === undefined) {
    return '-'
  }
  return `${value.toFixed(2)} tok/s`
}

export function StatusBar({ stage, connected, turnCount, sttPreview, ttsQueueSize, recording, ttsProviderLabel, llmStats }: StatusBarProps) {
  const progress = Math.min(100, Math.round((turnCount / 12) * 100))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">状态面板</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <Badge variant={connected ? 'success' : 'warning'}>{connected ? '已连接' : '重连中'}</Badge>
          <Badge variant="secondary">{stageTextMap[stage]}</Badge>
          <Badge variant={recording ? 'default' : 'secondary'}>{recording ? '录音中' : '待录音'}</Badge>
        </div>

        <div className="space-y-2">
          <p className="text-xs text-slate-400">面试进度（预估）</p>
          <Progress value={progress} />
          <p className="text-xs text-slate-500">当前轮次：{turnCount}</p>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-slate-400">语音识别预览</p>
          <p className="min-h-12 rounded-md border border-slate-800 bg-slate-950/70 px-2 py-2 text-xs text-slate-300">
            {sttPreview || '等待语音输入...'}
          </p>
        </div>

        <p className="text-xs text-slate-500">TTS 队列：{ttsQueueSize} 段</p>
        <p className="text-xs text-slate-500">当前 TTS 通道：{ttsProviderLabel}</p>

        <Separator />

        <div className="space-y-2">
          <p className="text-xs text-slate-400">本轮 LLM 生成统计</p>
          {llmStats ? (
            <div className="space-y-1 rounded-md border border-slate-800 bg-slate-950/60 px-2 py-2 text-xs text-slate-300">
              <p>通道：{llmStats.backend}</p>
              <p>首 token 延迟：{fmtSeconds(llmStats.first_token_seconds)}</p>
              <p>总耗时：{fmtSeconds(llmStats.total_seconds)}</p>
              <p>生成速率：{fmtTps(llmStats.tokens_per_second)}</p>
              <p>Prompt Tokens：{fmtNumber(llmStats.prompt_tokens)}</p>
              <p>Generated Tokens：{fmtNumber(llmStats.generated_tokens)}</p>
              <p>Generated Chars：{fmtNumber(llmStats.generated_chars)}</p>
              <p>停止原因：{llmStats.done_reason ?? '-'}</p>
            </div>
          ) : (
            <p className="rounded-md border border-slate-800 bg-slate-950/60 px-2 py-2 text-xs text-slate-500">等待本轮 LLM 输出...</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

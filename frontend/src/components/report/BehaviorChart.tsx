import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface BehaviorChartProps {
  behaviorScore: number
  behaviorDetail?: {
    sample_count?: number
    attention_score?: number
    posture_score?: number
    engagement_score?: number
    gaze_stability?: number
    recommendations?: string[]
  }
}

const display = (value?: number) => (typeof value === 'number' ? `${Math.round(value)}%` : '-')

export function BehaviorChart({ behaviorScore, behaviorDetail }: BehaviorChartProps) {
  const normalized = Math.max(0, Math.min(100, behaviorScore))
  const recommendations = behaviorDetail?.recommendations ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-neutral-300">行为表现概览</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative h-3 w-full overflow-hidden rounded-full bg-neutral-800">
          <div className="h-full bg-neutral-500 transition-all duration-700" style={{ width: `${normalized}%` }} />
        </div>

        <div className="grid gap-2 md:grid-cols-4">
          <Metric title="注意力" value={display(behaviorDetail?.attention_score)} />
          <Metric title="姿态稳定" value={display(behaviorDetail?.posture_score)} />
          <Metric title="互动投入" value={display(behaviorDetail?.engagement_score)} />
          <Metric title="视线稳定" value={display(behaviorDetail?.gaze_stability)} />
        </div>

        <p className="text-xs text-neutral-500">采样帧数：{behaviorDetail?.sample_count ?? 0}</p>

        {recommendations.length > 0 ? (
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-widest text-neutral-400">行为改进建议</p>
            <ul className="space-y-1 text-xs text-neutral-300">
              {recommendations.map((item, idx) => (
                <li key={idx}>- {item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-md border border-neutral-800 bg-neutral-950/70 p-2">
      <p className="text-[11px] text-neutral-400">{title}</p>
      <p className="text-sm font-semibold text-neutral-100">{value}</p>
    </div>
  )
}

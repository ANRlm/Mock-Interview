import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface BehaviorChartProps {
  behaviorScore: number
}

export function BehaviorChart({ behaviorScore }: BehaviorChartProps) {
  const normalized = Math.max(0, Math.min(100, behaviorScore))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-slate-300">行为表现概览</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative h-3 w-full overflow-hidden rounded-full bg-slate-800">
          <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-700" style={{ width: `${normalized}%` }} />
        </div>
        <p className="mt-3 text-xs text-slate-500">基于眼神接触与姿态稳定性（Phase 1 为预留值）</p>
      </CardContent>
    </Card>
  )
}

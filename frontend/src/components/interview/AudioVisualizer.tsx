import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface AudioVisualizerProps {
  level: number
  active: boolean
}

export function AudioVisualizer({ level, active }: AudioVisualizerProps) {
  const normalized = Math.max(0, Math.min(1, level))
  const bars = Array.from({ length: 12 }).map((_, index) => {
    const phase = (index % 4) * 0.14
    const base = 0.16 + phase
    const value = active ? base + normalized * (0.7 - phase * 0.4) : base * 0.6
    return Math.max(0.08, Math.min(0.95, value))
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">音频波形</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex h-20 items-end gap-1 rounded-lg border border-slate-800 bg-slate-950/80 p-3">
          {bars.map((height, index) => (
            <span
              key={index}
              className={`w-full rounded-sm bg-gradient-to-t transition-all duration-100 ${
                active ? 'from-blue-500/80 to-cyan-300' : 'from-slate-700 to-slate-500'
              }`}
              style={{ height: `${Math.round(height * 100)}%` }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

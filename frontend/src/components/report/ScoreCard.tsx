import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface ScoreCardProps {
  title: string
  value: number
  caption: string
}

export function ScoreCard({ title, value, caption }: ScoreCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-slate-300">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-slate-100">{Math.round(value)}</p>
        <p className="mt-2 text-xs text-slate-500">{caption}</p>
      </CardContent>
    </Card>
  )
}

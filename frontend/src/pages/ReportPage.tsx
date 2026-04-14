import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { api } from '@/services/api'

interface Report {
  session_id: string
  total_score: number
  llm_overall_score?: number
  llm_professional_score?: number
  llm_communication_score?: number
  llm_logic_score?: number
  fluency_score?: number
  behavior_score?: number
  strengths?: string[]
  improvements?: string[]
  generated_at: string
}

export function ReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!sessionId) return

    const fetchReport = async () => {
      try {
        const data = await api.get<Report>(`/sessions/${sessionId}/report`)
        setReport(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取报告失败')
      } finally {
        setLoading(false)
      }
    }

    fetchReport()
  }, [sessionId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="text-center space-y-4">
        <p className="text-text-muted">{error || '报告不存在'}</p>
        <Button variant="secondary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </div>
    )
  }

  const scores = [
    { label: '综合评分', value: report.llm_overall_score, max: 100 },
    { label: '专业能力', value: report.llm_professional_score, max: 100 },
    { label: '沟通表达', value: report.llm_communication_score, max: 100 },
    { label: '逻辑思维', value: report.llm_logic_score, max: 100 },
    { label: '流畅度', value: report.fluency_score, max: 100 },
    { label: '行为分析', value: report.behavior_score, max: 100 },
  ].filter((s) => s.value !== undefined)

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-text">面试报告</h1>
        <p className="text-text-muted">
          生成时间：{new Date(report.generated_at).toLocaleString('zh-CN')}
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">综合得分</h2>
            <Badge variant={report.total_score >= 70 ? 'success' : report.total_score >= 50 ? 'warning' : 'error'}>
              {report.total_score.toFixed(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <span className="text-7xl font-bold text-text">{report.total_score.toFixed(0)}</span>
            <span className="text-2xl text-text-muted">/100</span>
          </div>
        </CardContent>
      </Card>

      {scores.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-medium">分项评分</h2>
          </CardHeader>
          <CardContent className="space-y-4">
            {scores.map((score) => (
              <div key={score.label} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">{score.label}</span>
                  <span className="font-medium text-text">
                    {score.value?.toFixed(1)} / {score.max}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-surface">
                  <div
                    className="h-2 rounded-full bg-primary transition-all"
                    style={{ width: `${((score.value ?? 0) / score.max) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {report.strengths && report.strengths.length > 0 && (
          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium text-green-600">优点</h2>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {report.strengths.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-text">
                    <span className="text-green-500">+</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {report.improvements && report.improvements.length > 0 && (
          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium text-amber-600">改进建议</h2>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {report.improvements.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-text">
                    <span className="text-amber-500">→</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="flex justify-center">
        <Button variant="secondary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </div>
    </div>
  )
}
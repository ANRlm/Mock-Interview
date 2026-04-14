import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { BehaviorChart } from '@/components/report/BehaviorChart'
import { ScoreCard } from '@/components/report/ScoreCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getReport, triggerReport } from '@/services/api'
import { useInterviewStore } from '@/stores/interviewStore'

interface ReportPageViewProps {
  sessionId: string
}

export function ReportPageView({ sessionId }: ReportPageViewProps) {
  const navigate = useNavigate()
  const { report, setReport } = useInterviewStore()
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('正在生成报告...')

  useEffect(() => {
    let cancelled = false

    const run = async () => {
      await triggerReport(sessionId)

      for (let i = 0; i < 20; i += 1) {
        const data = await getReport(sessionId)
        if (cancelled) {
          return
        }
        if (data) {
          setReport(data)
          setLoading(false)
          return
        }
        await new Promise((resolve) => window.setTimeout(resolve, 1200))
      }

      if (!cancelled) {
        setLoading(false)
        setMessage('报告生成超时，请稍后重试。')
      }
    }

    run().catch(() => {
      if (!cancelled) {
        setLoading(false)
        setMessage('报告生成失败，请检查后端服务。')
      }
    })

    return () => {
      cancelled = true
    }
  }, [sessionId, setReport])

  const currentReport = useMemo(() => {
    if (!report) {
      return null
    }
    return report.session_id === sessionId ? report : null
  }, [report, sessionId])

  const generatedAt = useMemo(() => {
    if (!currentReport) {
      return '-'
    }
    return new Date(currentReport.generated_at).toLocaleString()
  }, [currentReport])

  if (loading || !currentReport) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>面试报告</CardTitle>
          <CardDescription>{message}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-800">
            <div className="h-full w-1/2 animate-pulse bg-neutral-500" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-xl">综合评分 {Math.round(currentReport.total_score)}</CardTitle>
            <CardDescription>生成时间：{generatedAt}</CardDescription>
          </div>
          <Button variant="outline" onClick={() => navigate('/')}>
            返回首页
          </Button>
        </CardHeader>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <ScoreCard title="专业能力" value={currentReport.llm_professional_score} caption="知识体系与实践深度" />
        <ScoreCard title="沟通表达" value={currentReport.llm_communication_score} caption="表达结构与清晰度" />
        <ScoreCard title="逻辑思维" value={currentReport.llm_logic_score} caption="分析路径与论证一致性" />
      </div>

      <BehaviorChart behaviorScore={currentReport.behavior_score} behaviorDetail={currentReport.behavior_detail} />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">面试官总结</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-neutral-300">
          <p>{currentReport.llm_evaluation_text}</p>

          <div>
            <p className="mb-1 text-xs uppercase tracking-widest text-neutral-400">优势</p>
            <ul className="space-y-1 text-neutral-300">
              {currentReport.strengths.map((item, idx) => (
                <li key={idx}>- {item}</li>
              ))}
            </ul>
          </div>

          <div>
            <p className="mb-1 text-xs uppercase tracking-widest text-neutral-400">改进建议</p>
            <ul className="space-y-1 text-neutral-300">
              {currentReport.improvements.map((item, idx) => (
                <li key={idx}>- {item}</li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

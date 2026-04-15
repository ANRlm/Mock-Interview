import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { motion } from 'framer-motion'
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
      <motion.div 
        className="max-w-md mx-auto text-center space-y-6 p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="w-16 h-16 rounded-full bg-error/10 mx-auto flex items-center justify-center">
          <span className="text-2xl">📋</span>
        </div>
        <p className="text-text-muted">{error || '报告不存在'}</p>
        <Button variant="secondary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </motion.div>
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

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.08 }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-success'
    if (score >= 60) return 'text-warning'
    return 'text-error'
  }

  return (
    <motion.div 
      className="max-w-4xl mx-auto space-y-8 p-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div className="text-center space-y-3" variants={itemVariants}>
        <h1 className="text-heading-40 font-bold text-text">面试报告</h1>
        <p className="text-label-16 text-text-muted">
          生成时间：{new Date(report.generated_at).toLocaleString('zh-CN')}
        </p>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card className="shadow-elevation-2 overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-primary/10 to-transparent">
            <div className="flex items-center justify-between">
              <h2 className="text-heading-24 font-semibold">综合得分</h2>
              <Badge 
                variant={report.total_score >= 70 ? 'success' : report.total_score >= 50 ? 'warning' : 'error'}
                className="text-base px-3 py-1"
              >
                {report.total_score.toFixed(1)}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="py-10">
            <motion.div 
              className="text-center"
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 20 }}
            >
              <span className={`text-8xl font-bold ${getScoreColor(report.total_score)}`}>
                {report.total_score.toFixed(0)}
              </span>
              <span className="text-3xl text-text-muted">/100</span>
            </motion.div>
          </CardContent>
        </Card>
      </motion.div>

      {scores.length > 0 && (
        <motion.div variants={itemVariants}>
          <Card className="shadow-elevation-2">
            <CardHeader>
              <h2 className="text-heading-24 font-semibold">分项评分</h2>
            </CardHeader>
            <CardContent className="space-y-6">
              {scores.map((score, index) => (
                <motion.div 
                  key={score.label}
                  className="space-y-3"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="flex justify-between text-sm">
                    <span className="font-medium text-text">{score.label}</span>
                    <span className={`font-semibold ${getScoreColor(score.value || 0)}`}>
                      {score.value?.toFixed(1)} / {score.max}
                    </span>
                  </div>
                  <div className="h-3 bg-surface rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${((score.value ?? 0) / score.max) * 100}%` }}
                      transition={{ duration: 0.8, delay: 0.2 + index * 0.1, ease: 'easeOut' }}
                      className={`h-full rounded-full ${
                        (score.value ?? 0) >= 80 ? 'bg-success' :
                        (score.value ?? 0) >= 60 ? 'bg-warning' : 'bg-error'
                      }`}
                    />
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {report.strengths && report.strengths.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card className="shadow-elevation-2 h-full">
              <CardHeader className="bg-success/5">
                <h2 className="text-heading-24 font-semibold text-success">💪 优点</h2>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {report.strengths.map((item, i) => (
                    <motion.li 
                      key={i} 
                      className="flex items-start gap-3 text-text"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <span className="w-6 h-6 rounded-full bg-success/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-success text-sm">✓</span>
                      </span>
                      <span className="text-label-16 leading-relaxed">{item}</span>
                    </motion.li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {report.improvements && report.improvements.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card className="shadow-elevation-2 h-full">
              <CardHeader className="bg-warning/5">
                <h2 className="text-heading-24 font-semibold text-warning">💡 改进建议</h2>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {report.improvements.map((item, i) => (
                    <motion.li 
                      key={i} 
                      className="flex items-start gap-3 text-text"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <span className="w-6 h-6 rounded-full bg-warning/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-warning text-sm">→</span>
                      </span>
                      <span className="text-label-16 leading-relaxed">{item}</span>
                    </motion.li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>

      <motion.div className="flex justify-center" variants={itemVariants}>
        <Button variant="secondary" size="lg" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </motion.div>
    </motion.div>
  )
}

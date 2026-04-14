import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Code, Briefcase, Stethoscope, GraduationCap } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { api } from '@/services/api'
import { HeroSection } from '@/components/landing/HeroSection'
import { HowItWorksSection } from '@/components/landing/HowItWorksSection'
import { FeaturesSection } from '@/components/landing/FeaturesSection'
import { TechSection } from '@/components/landing/TechSection'
import { ArchitectureSection } from '@/components/landing/ArchitectureSection'
import { MetricsSection } from '@/components/landing/MetricsSection'

const roles = [
  { id: 'programmer', label: '程序员', icon: Code, desc: '前端/后端/全栈开发' },
  { id: 'lawyer', label: '律师', icon: Briefcase, desc: '法律咨询与诉讼' },
  { id: 'doctor', label: '医生', icon: Stethoscope, desc: '临床医学与诊断' },
  { id: 'teacher', label: '教师', icon: GraduationCap, desc: '教育教学技能' },
]

interface Session {
  id: string
  job_role: string
  sub_role?: string
  status: string
  created_at: string
}

export function HomePage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<Session[]>([])

  useEffect(() => {
    api.get<Session[]>('/sessions').then(setSessions).catch(() => {})
  }, [])

  return (
    <div className="space-y-12">
      <HeroSection />
      <HowItWorksSection />
      <FeaturesSection />
      <TechSection />
      <ArchitectureSection />
      <MetricsSection />

      {sessions.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-medium text-text">最近的面试</h2>
          <div className="space-y-2">
            {sessions.slice(0, 5).map((session) => (
              <Card
                key={session.id}
                className="cursor-pointer hover:bg-surface/50"
                onClick={() => navigate(`/interview/${session.id}`)}
              >
                <CardContent className="flex items-center justify-between p-4">
                  <div>
                    <p className="font-medium text-text">
                      {roles.find((r) => r.id === session.job_role)?.label || session.job_role}
                      {session.sub_role && ` · ${session.sub_role}`}
                    </p>
                    <p className="text-sm text-text-muted">
                      {new Date(session.created_at).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                  <Badge
                    variant={
                      session.status === 'completed'
                        ? 'success'
                        : session.status === 'active'
                        ? 'warning'
                        : 'default'
                    }
                  >
                    {session.status === 'completed'
                      ? '已完成'
                      : session.status === 'active'
                      ? '进行中'
                      : '未开始'}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
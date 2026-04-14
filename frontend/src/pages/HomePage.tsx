import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Code, Briefcase, Stethoscope, GraduationCap, Plus } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { api } from '@/services/api'

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
  const [selectedRole, setSelectedRole] = useState<string | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])

  useEffect(() => {
    api.get<Session[]>('/sessions').then(setSessions).catch(() => {})
  }, [])

  const handleStartInterview = () => {
    if (selectedRole) {
      navigate('/setup', { state: { role: selectedRole } })
    }
  }

  return (
    <div className="space-y-12">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight text-text">
          AI 模拟面试
        </h1>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto">
          选择一个角色，开始一场真实的模拟面试。AI 面试官将根据你的简历和回答给出专业反馈。
        </p>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-medium text-text">选择面试角色</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {roles.map((role) => {
            const Icon = role.icon
            return (
              <Card
                key={role.id}
                className={`cursor-pointer transition-all hover:shadow-geist-md ${
                  selectedRole === role.id
                    ? 'ring-2 ring-primary border-primary'
                    : ''
                }`}
                onClick={() => setSelectedRole(role.id)}
              >
                <CardContent className="flex flex-col items-center gap-3 p-6">
                  <div className="rounded-full bg-surface p-4">
                    <Icon size={32} className="text-text" />
                  </div>
                  <div className="text-center">
                    <p className="font-medium text-text">{role.label}</p>
                    <p className="text-sm text-text-muted mt-1">{role.desc}</p>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
        <div className="flex justify-center">
          <Button
            size="lg"
            disabled={!selectedRole}
            onClick={handleStartInterview}
          >
            <Plus size={18} className="mr-2" />
            开始面试
          </Button>
        </div>
      </div>

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
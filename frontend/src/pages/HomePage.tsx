import { ArrowRight, BriefcaseBusiness, Gavel, HeartPulse, School } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useSettingsStore } from '@/stores/settingsStore'
import type { JobRole } from '@/types/interview'

const cards: { role: JobRole; title: string; desc: string; icon: typeof BriefcaseBusiness }[] = [
  { role: 'programmer', title: '程序员面试', desc: '算法、系统设计、项目复盘', icon: BriefcaseBusiness },
  { role: 'lawyer', title: '律师面试', desc: '法条理解、案情推理、抗压表达', icon: Gavel },
  { role: 'doctor', title: '医生面试', desc: '临床判断、病历思维、沟通协作', icon: HeartPulse },
  { role: 'teacher', title: '教师面试', desc: '教学设计、课堂管理、情境互动', icon: School },
]

export function HomePage() {
  const navigate = useNavigate()
  const { setRole } = useSettingsStore()

  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.22),transparent_45%),radial-gradient(circle_at_80%_0%,rgba(14,165,233,0.18),transparent_40%),#070b13] p-8 md:p-10">
        <Badge variant="secondary">Local-first AI Interview</Badge>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-100 md:text-4xl">沉浸式模拟面试系统</h1>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-slate-300">
          先从文本模式完成一轮完整面试闭环，后续可无缝扩展语音、视觉行为分析与简历驱动提问。
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Button onClick={() => navigate('/setup')}>
            开始面试
            <ArrowRight className="ml-2" size={16} />
          </Button>
          <Button variant="outline" onClick={() => navigate('/report/latest')}>
            查看最近报告
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {cards.map((item) => {
          const Icon = item.icon
          return (
            <Card key={item.role} className="group transition-colors hover:border-blue-500/40">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Icon size={18} className="text-blue-300" />
                  {item.title}
                </CardTitle>
                <CardDescription>{item.desc}</CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <Button
                  variant="ghost"
                  className="px-0 text-blue-300 group-hover:text-blue-200"
                  onClick={() => {
                    setRole(item.role)
                    navigate('/setup')
                  }}
                >
                  选择此方向
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </section>
    </div>
  )
}

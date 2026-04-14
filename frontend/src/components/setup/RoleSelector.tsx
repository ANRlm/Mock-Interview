'use client'

import { Code, Briefcase, Stethoscope, GraduationCap } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'

const roles = [
  { id: 'programmer', label: '程序员', icon: Code, desc: '前端/后端/全栈开发' },
  { id: 'lawyer', label: '律师', icon: Briefcase, desc: '法律咨询与诉讼' },
  { id: 'doctor', label: '医生', icon: Stethoscope, desc: '临床医学与诊断' },
  { id: 'teacher', label: '教师', icon: GraduationCap, desc: '教育教学技能' },
]

interface RoleSelectorProps {
  selectedRole: string | null
  onSelect: (role: string) => void
}

export function RoleSelector({ selectedRole, onSelect }: RoleSelectorProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {roles.map((role) => {
        const Icon = role.icon
        return (
          <Card
            key={role.id}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedRole === role.id
                ? 'ring-2 ring-primary border-primary'
                : ''
            }`}
            onClick={() => onSelect(role.id)}
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
  )
}

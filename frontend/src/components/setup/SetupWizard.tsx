import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { useSettingsStore } from '@/stores/settingsStore'
import type { JobRole } from '@/types/interview'

import { ResumeUploader } from './ResumeUploader'
import { LlmRuntimePanel } from './LlmRuntimePanel'

const roleOptions: { role: JobRole; label: string; desc: string }[] = [
  { role: 'programmer', label: '程序员', desc: '算法、系统设计、项目深挖' },
  { role: 'lawyer', label: '律师', desc: '法条理解、案例推理、沟通抗压' },
  { role: 'doctor', label: '医生', desc: '临床思维、病历判断、医患沟通' },
  { role: 'teacher', label: '教师', desc: '教学设计、课堂管理、表达引导' },
]

export function SetupWizard() {
  const navigate = useNavigate()
  const { selectedRole, setRole, subRole, setSubRole, resumeFile, setResumeFile } = useSettingsStore()
  const [error, setError] = useState<string | null>(null)

  const handleStart = () => {
    if (resumeFile && resumeFile.size > 15 * 1024 * 1024) {
      setError('简历文件请控制在 15MB 以内。')
      return
    }

    setError(null)
    navigate('/interview')
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>面试配置</CardTitle>
          <CardDescription>选择岗位方向并填写细分职位，立即进入文本模拟面试。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-neutral-200">1. 选择职位方向</h3>
            <div className="grid gap-3 md:grid-cols-2">
              {roleOptions.map((option) => (
                <button
                  type="button"
                  key={option.role}
                  className={`rounded-xl border px-4 py-3 text-left transition-colors ${
                    selectedRole === option.role
                      ? 'border-neutral-500 bg-neutral-800/80'
                      : 'border-neutral-800 bg-neutral-950/40 hover:border-neutral-700'
                  }`}
                  onClick={() => setRole(option.role)}
                >
                  <p className="text-sm font-semibold text-neutral-100">{option.label}</p>
                  <p className="mt-1 text-xs text-neutral-400">{option.desc}</p>
                </button>
              ))}
            </div>
          </section>

          <Separator />

          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-neutral-200">2. 细分职位（可选）</h3>
            <Input placeholder="例如：前端工程师 / 刑事律师 / 内科医生" value={subRole} onChange={(e) => setSubRole(e.target.value)} />
          </section>

          <Separator />

          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-neutral-200">3. 简历上传（预留）</h3>
            <ResumeUploader file={resumeFile} onFileChange={setResumeFile} />
          </section>

          {error ? <p className="text-sm text-rose-400">{error}</p> : null}

          <div className="flex justify-end">
            <Button onClick={handleStart}>开始面试</Button>
          </div>
        </CardContent>
      </Card>

      <LlmRuntimePanel />
    </div>
  )
}

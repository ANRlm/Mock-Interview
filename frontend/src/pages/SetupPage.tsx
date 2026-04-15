import { useState, useEffect, useRef, type DragEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Upload, FileText, Settings, Code, Briefcase, Stethoscope, GraduationCap } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'

const roles = [
  { id: 'programmer', label: '程序员', icon: Code, desc: '前端/后端/全栈开发' },
  { id: 'lawyer', label: '律师', icon: Briefcase, desc: '法律咨询与诉讼' },
  { id: 'doctor', label: '医生', icon: Stethoscope, desc: '临床医学与诊断' },
  { id: 'teacher', label: '教师', icon: GraduationCap, desc: '教育教学技能' },
]

function LoginPromptModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate()

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-surface rounded-lg border border-border shadow-elevation-2 p-6 w-full max-w-sm mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-heading-24 font-semibold text-text mb-2">请先登录</h2>
        <p className="text-copy-16 text-text-secondary mb-6">登录后可创建面试会话</p>
        <div className="flex gap-3">
          <Button variant="secondary" size="lg" className="flex-1" onClick={onClose}>
            取消
          </Button>
          <Button size="lg" className="flex-1" onClick={() => navigate('/login')}>
            去登录
          </Button>
        </div>
      </motion.div>
    </div>
  )
}

export function SetupPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated } = useAuthStore()
  const [jobRole, setJobRole] = useState<string>('programmer')
  const [subRole, setSubRole] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [resumeStatus, setResumeStatus] = useState<'empty' | 'uploaded'>('empty')
  const [uploading, setUploading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [llmConfig, setLlmConfig] = useState<Record<string, unknown>>({})
  const [showLoginModal, setShowLoginModal] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (location.state?.role) {
      setJobRole(location.state.role)
    }
    api.get<Record<string, unknown>>('/llm/profiles').then(setLlmConfig).catch(() => {})
  }, [location.state])

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      setResumeFile(file)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setResumeFile(file)
    }
  }

  const handleUploadResume = async () => {
    if (!resumeFile) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', resumeFile)
      await api.postForm('/sessions/_resume_temp_/resume', formData)
      setResumeStatus('uploaded')
    } catch {
    } finally {
      setUploading(false)
    }
  }

  const handleStartInterview = async () => {
    if (!isAuthenticated) {
      setShowLoginModal(true)
      return
    }
    setCreating(true)
    setError('')
    try {
      const session = await api.post<{ id: string }>('/sessions', {
        job_role: jobRole,
        sub_role: subRole || undefined,
      })
      if (resumeFile) {
        const formData = new FormData()
        formData.append('file', resumeFile)
        await api.postForm(`/sessions/${session.id}/resume`, formData)
      }
      navigate(`/interview/${session.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setCreating(false)
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  }

  return (
    <motion.div
      className="max-w-2xl mx-auto space-y-8 p-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div className="text-center space-y-3" variants={itemVariants}>
        <h1 className="text-heading-40 font-bold text-text">准备面试</h1>
        <p className="text-copy-18 text-text-secondary">上传简历并配置面试参数</p>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card className="shadow-elevation-2">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Settings size={20} className="text-primary" />
              </div>
              <div>
                <h2 className="text-heading-24 font-semibold">选择职位类型</h2>
                <p className="text-label-14 text-text-muted">选择你想要练习的职位</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {roles.map((role, index) => {
                const Icon = role.icon
                const isSelected = jobRole === role.id
                return (
                  <motion.button
                    key={role.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05, duration: 0.2 }}
                    onClick={() => setJobRole(role.id)}
                    className={cn(
                      'flex flex-col items-center gap-3 p-5 rounded-xl border-2 transition-all duration-fast text-center',
                      isSelected
                        ? 'border-primary bg-primary/10 text-primary shadow-elevation-2'
                        : 'border-border bg-surface hover:border-primary/50 text-text hover:shadow-elevation-1'
                    )}
                  >
                    <div className={cn(
                      'w-12 h-12 rounded-xl flex items-center justify-center transition-colors',
                      isSelected ? 'bg-primary/20' : 'bg-surface'
                    )}>
                      <Icon size={26} />
                    </div>
                    <span className="font-semibold text-base">{role.label}</span>
                    <span className="text-label-12 text-text-muted">{role.desc}</span>
                  </motion.button>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card className="shadow-elevation-2">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <FileText size={20} className="text-primary" />
              </div>
              <div>
                <h2 className="text-heading-24 font-semibold">简历上传</h2>
                <p className="text-label-14 text-text-muted">上传你的简历让 AI 更好地了解你</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <motion.div
              className={cn(
                'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-fast',
                'hover:border-primary/50 hover:bg-primary/5',
                resumeFile ? 'border-primary/50 bg-primary/5' : 'border-border'
              )}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.md"
                className="hidden"
                onChange={handleFileSelect}
              />
              {resumeFile ? (
                <div className="space-y-3">
                  <div className="w-16 h-16 rounded-xl bg-primary/10 mx-auto flex items-center justify-center">
                    <FileText size={28} className="text-primary" />
                  </div>
                  <p className="font-semibold text-text text-copy-20">{resumeFile.name}</p>
                  <p className="text-label-14 text-text-muted">
                    {(resumeFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="w-16 h-16 rounded-xl bg-surface mx-auto flex items-center justify-center">
                    <Upload size={28} className="text-text-muted" />
                  </div>
                  <p className="font-medium text-text">
                    拖拽简历文件或点击选择
                  </p>
                  <p className="text-label-14 text-text-muted">
                    支持 PDF、TXT、MD 格式
                  </p>
                </div>
              )}
            </motion.div>
            {resumeFile && (
              <motion.div
                className="flex items-center justify-between"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
              >
                <Badge variant={resumeStatus === 'uploaded' ? 'success' : 'default'}>
                  {resumeStatus === 'uploaded' ? '已解析' : '待上传'}
                </Badge>
                <Button variant="secondary" size="sm" onClick={handleUploadResume} loading={uploading}>
                  上传简历
                </Button>
              </motion.div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card className="shadow-elevation-2">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Settings size={20} className="text-primary" />
              </div>
              <div>
                <h2 className="text-heading-24 font-semibold">面试配置</h2>
                <p className="text-label-14 text-text-muted">自定义你的面试体验</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-3">
              <label className="text-label-14 font-semibold text-text">子角色（可选）</label>
              <Input
                placeholder="例如：前端工程师、全栈开发"
                value={subRole}
                onChange={(e) => setSubRole(e.target.value)}
              />
            </div>

            <div className="space-y-3">
              <label className="text-label-14 font-semibold text-text">LLM 配置</label>
              <div className="rounded-xl border border-border bg-surface p-4">
                {Object.keys(llmConfig).length > 0 ? (
                  <pre className="text-xs text-text-muted overflow-x-auto font-mono">{JSON.stringify(llmConfig, null, 2)}</pre>
                ) : (
                  <p className="text-label-14 text-text-muted">使用默认配置</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {error && (
        <motion.div
          className="text-center py-3 rounded-xl bg-error/10 border border-error/20"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <p className="text-label-14 text-error">{error}</p>
        </motion.div>
      )}

      <motion.div className="flex justify-center gap-4" variants={itemVariants}>
        <Button variant="secondary" size="lg" onClick={() => navigate('/')}>
          返回首页
        </Button>
        <Button size="lg" onClick={handleStartInterview} loading={creating}>
          开始面试
        </Button>
      </motion.div>

      <LoginPromptModal open={showLoginModal} onClose={() => setShowLoginModal(false)} />
    </motion.div>
  )
}
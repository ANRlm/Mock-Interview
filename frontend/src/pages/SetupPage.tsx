import { useState, useEffect, useRef, type DragEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Upload, FileText, Settings } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { api } from '@/services/api'

export function SetupPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [jobRole, setJobRole] = useState<string>('programmer')
  const [subRole, setSubRole] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [resumeStatus] = useState<'empty' | 'uploaded'>('empty')
  const [uploading, setUploading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [llmConfig, setLlmConfig] = useState<Record<string, unknown>>({})
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
    } catch {
    } finally {
      setUploading(false)
    }
  }

  const handleStartInterview = async () => {
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

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-text">准备面试</h1>
        <p className="text-text-secondary">上传简历并配置面试参数</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText size={20} />
            <h2 className="text-lg font-medium">简历上传</h2>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md"
              className="hidden"
              onChange={handleFileSelect}
            />
            {resumeFile ? (
              <div className="space-y-2">
                <p className="font-medium text-text">{resumeFile.name}</p>
                <p className="text-sm text-text-muted">
                  {(resumeFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload size={32} className="mx-auto text-text-muted" />
                <p className="text-text-secondary">
                  拖拽简历文件或点击选择
                </p>
                <p className="text-sm text-text-muted">
                  支持 PDF、TXT、MD 格式
                </p>
              </div>
            )}
          </div>
          {resumeFile && (
            <div className="flex items-center justify-between">
              <Badge variant={resumeStatus === 'uploaded' ? 'success' : 'default'}>
                {resumeStatus === 'uploaded' ? '已解析' : '待上传'}
              </Badge>
              <Button variant="secondary" size="sm" onClick={handleUploadResume} loading={uploading}>
                上传简历
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Settings size={20} />
            <h2 className="text-lg font-medium">面试配置</h2>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text">子角色（可选）</label>
            <Input
              placeholder="例如：前端工程师"
              value={subRole}
              onChange={(e) => setSubRole(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text">LLM 配置</label>
            <div className="rounded-md border border-border bg-surface p-4 text-sm text-text-muted">
              {Object.keys(llmConfig).length > 0
                ? JSON.stringify(llmConfig, null, 2)
                : '使用默认配置'}
            </div>
          </div>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-500 text-center">{error}</p>}

      <div className="flex justify-center gap-4">
        <Button variant="secondary" onClick={() => navigate('/')}>
          返回
        </Button>
        <Button onClick={handleStartInterview} loading={creating}>
          开始面试
        </Button>
      </div>
    </div>
  )
}
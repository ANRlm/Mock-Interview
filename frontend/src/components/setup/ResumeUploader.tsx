import { type ChangeEvent, useRef } from 'react'
import { FileText, Upload, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface ResumeUploaderProps {
  file: File | null
  onFileChange: (file: File | null) => void
  disabled?: boolean
}

const toReadableSize = (bytes: number): string => {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function ResumeUploader({ file, onFileChange, disabled = false }: ResumeUploaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)

  const handleSelectFile = () => {
    inputRef.current?.click()
  }

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null
    onFileChange(nextFile)
  }

  const clearFile = () => {
    onFileChange(null)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  return (
    <Card className="border-dashed">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Upload size={16} />
          简历上传
        </CardTitle>
        <CardDescription>支持 .pdf / .txt / .md。上传后会在创建面试会话后自动解析。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <input ref={inputRef} type="file" accept=".pdf,.txt,.md" className="hidden" onChange={handleInputChange} />

        <div className="rounded-lg border border-neutral-800 bg-neutral-950/50 p-3">
          {file ? (
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-2">
                <FileText size={16} className="text-neutral-400" />
                <div className="min-w-0">
                  <p className="truncate text-sm text-neutral-100">{file.name}</p>
                  <p className="text-xs text-neutral-400">{toReadableSize(file.size)}</p>
                </div>
              </div>
              <Button type="button" variant="ghost" size="sm" disabled={disabled} onClick={clearFile}>
                <X size={14} />
              </Button>
            </div>
          ) : (
            <p className="text-xs text-neutral-400">未选择文件，可跳过直接开始面试。</p>
          )}
        </div>

        <Button type="button" variant="outline" size="sm" disabled={disabled} onClick={handleSelectFile}>
          {file ? '重新选择文件' : '选择简历文件'}
        </Button>
      </CardContent>
    </Card>
  )
}

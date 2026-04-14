'use client'

import { useCallback, useState } from 'react'
import { Upload, File, X } from 'lucide-react'

interface ResumeUploaderProps {
  onUpload: (file: File) => void
  onClear?: () => void
}

export function ResumeUploader({ onUpload, onClear }: ResumeUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && (droppedFile.type === 'application/pdf' || 
        droppedFile.type === 'text/plain' || 
        droppedFile.name.endsWith('.md'))) {
      setFile(droppedFile)
      onUpload(droppedFile)
    }
  }, [onUpload])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      onUpload(selectedFile)
    }
  }, [onUpload])

  const handleClear = useCallback(() => {
    setFile(null)
    onClear?.()
  }, [onClear])

  if (file) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-lg border border-border bg-surface/50">
        <File size={24} className="text-text-secondary" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text truncate">{file.name}</p>
          <p className="text-xs text-text-muted">{(file.size / 1024).toFixed(1)} KB</p>
        </div>
        <button
          onClick={handleClear}
          className="p-1 hover:bg-surface rounded-full transition-colors"
        >
          <X size={18} className="text-text-secondary" />
        </button>
      </div>
    )
  }

  return (
    <div
      className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
      }`}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".pdf,.txt,.md"
        onChange={handleFileSelect}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      <Upload size={32} className="mx-auto mb-3 text-text-secondary" />
      <p className="text-sm text-text">
        拖拽简历到此处，或 <span className="text-primary">点击选择</span>
      </p>
      <p className="text-xs text-text-muted mt-1">支持 PDF、TXT、MD 格式</p>
    </div>
  )
}

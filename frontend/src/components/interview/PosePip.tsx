import { useCallback, useEffect, useRef, useState } from 'react'

import { useMediaPipe } from '@/hooks/useMediaPipe'

interface Position {
  x: number
  y: number
}

const PIP_STORAGE_KEY = 'pose-pip-position'

function getStoredPosition(): Position {
  try {
    const stored = localStorage.getItem(PIP_STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch {}
  return { x: window.innerWidth - 320, y: window.innerHeight - 280 }
}

function storePosition(pos: Position) {
  try {
    localStorage.setItem(PIP_STORAGE_KEY, JSON.stringify(pos))
  } catch {}
}

function asPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function PosePip() {
  const mediaPipe = useMediaPipe()
  const [minimized, setMinimized] = useState(false)
  const [position, setPosition] = useState<Position>(() => getStoredPosition())
  const [dragging, setDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)

  useEffect(() => {
    mediaPipe.start()
    return () => {
      mediaPipe.stop()
    }
  }, [])

  useEffect(() => {
    if (mediaPipe.ready && !videoRef.current) {
      videoRef.current = document.createElement('video')
      if (videoRef.current) {
        videoRef.current.muted = true
        videoRef.current.playsInline = true
        videoRef.current.className = 'w-full h-full object-cover rounded-lg'
      }
    }
    if (videoRef.current && mediaPipe.cameraEnabled) {
      const stream = (window as unknown as { __test_stream?: MediaStream }).__test_stream
      if (stream) {
        videoRef.current.srcObject = stream
      }
    }
  }, [mediaPipe.ready, mediaPipe.cameraEnabled])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return
    setDragging(true)
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    })
  }, [position])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!dragging) return
    const newX = Math.max(0, Math.min(window.innerWidth - 300, e.clientX - dragOffset.x))
    const newY = Math.max(0, Math.min(window.innerHeight - 200, e.clientY - dragOffset.y))
    setPosition({ x: newX, y: newY })
  }, [dragging, dragOffset])

  const handleMouseUp = useCallback(() => {
    if (dragging) {
      setDragging(false)
      storePosition(position)
    }
  }, [dragging, position])

  useEffect(() => {
    if (dragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [dragging, handleMouseMove, handleMouseUp])

  if (minimized) {
    return (
      <button
        onClick={() => setMinimized(false)}
        className="fixed bottom-4 right-4 w-12 h-12 rounded-full bg-neutral-800 border border-neutral-700 flex items-center justify-center text-neutral-300 hover:bg-neutral-700 transition-colors z-50"
        style={{ left: position.x, top: position.y }}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      </button>
    )
  }

  return (
    <div
      ref={containerRef}
      className="fixed bg-neutral-900 border border-neutral-700 rounded-xl shadow-2xl z-50 overflow-hidden"
      style={{
        left: position.x,
        top: position.y,
        width: 280,
        cursor: dragging ? 'grabbing' : 'grab',
      }}
      onMouseDown={handleMouseDown}
    >
      <div className="flex items-center justify-between px-3 py-2 border-b border-neutral-800">
        <span className="text-sm font-medium text-neutral-200">摄像头预览</span>
        <div className="flex items-center gap-2">
          {mediaPipe.ready ? (
            <span className="w-2 h-2 rounded-full bg-neutral-500 animate-pulse" />
          ) : (
            <span className="w-2 h-2 rounded-full bg-neutral-600" />
          )}
          <button
            onClick={() => setMinimized(true)}
            className="p-1 rounded hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
        </div>
      </div>

      <div className="aspect-video bg-neutral-950 relative">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        {!mediaPipe.ready && (
          <div className="absolute inset-0 flex items-center justify-center bg-neutral-900/80">
            <span className="text-sm text-neutral-400">
              {mediaPipe.warning ? '摄像头错误' : '等待授权'}
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2 px-3 py-3">
        <div className="text-center">
          <div className="text-lg font-semibold text-neutral-100">
            {mediaPipe.ready ? asPercent(mediaPipe.eyeContactScore) : '--'}
          </div>
          <div className="text-xs text-neutral-500">注视</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-neutral-100">
            {mediaPipe.ready ? asPercent(mediaPipe.headPoseScore) : '--'}
          </div>
          <div className="text-xs text-neutral-500">姿态</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-neutral-100 capitalize">
            {mediaPipe.ready ? mediaPipe.expression : '--'}
          </div>
          <div className="text-xs text-neutral-500">表情</div>
        </div>
      </div>

      {mediaPipe.warning && (
        <div className="px-3 pb-3">
          <div className="text-xs text-neutral-400 bg-neutral-800 rounded px-2 py-1">
            {mediaPipe.warning}
          </div>
        </div>
      )}
    </div>
  )
}

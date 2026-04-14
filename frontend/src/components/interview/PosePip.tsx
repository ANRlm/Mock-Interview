import { useCallback, useEffect, useRef, useState } from 'react'

interface Position {
  x: number
  y: number
}

const PIP_STORAGE_KEY = 'pose-pip-position'

function getStoredPosition(): Position {
  try {
    const stored = localStorage.getItem(PIP_STORAGE_KEY)
    if (stored) return JSON.parse(stored)
  } catch {}
  return { x: window.innerWidth - 320, y: window.innerHeight - 280 }
}

function storePosition(pos: Position) {
  try {
    localStorage.setItem(PIP_STORAGE_KEY, JSON.stringify(pos))
  } catch {}
}

export function PosePip() {
  const [minimized, setMinimized] = useState(false)
  const [position, setPosition] = useState<Position>(() => getStoredPosition())
  const [dragging, setDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = (e: React.MouseEvent) => {
    setDragging(true)
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    })
  }

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

  return (
    <div
      ref={containerRef}
      className="fixed z-50 rounded-lg border border-border bg-surface shadow-geist-lg overflow-hidden"
      style={{
        left: position.x,
        top: position.y,
        width: minimized ? '80px' : '280px',
        height: minimized ? '80px' : '200px',
        transition: dragging ? 'none' : 'width 0.2s, height 0.2s',
      }}
    >
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-border cursor-move bg-surface"
        onMouseDown={handleMouseDown}
      >
        <span className="text-xs font-medium text-text">姿态检测</span>
        <button
          className="text-xs text-text-muted hover:text-text"
          onClick={() => setMinimized(!minimized)}
        >
          {minimized ? '展开' : '收起'}
        </button>
      </div>
      {!minimized && (
        <div className="p-3 space-y-2">
          <div className="aspect-video bg-bg rounded-md flex items-center justify-center">
            <span className="text-xs text-text-muted">摄像头画面</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-bg rounded px-2 py-1">
              <span className="text-text-muted">视线: </span>
              <span className="text-text">--</span>
            </div>
            <div className="bg-bg rounded px-2 py-1">
              <span className="text-text-muted">姿态: </span>
              <span className="text-text">--</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
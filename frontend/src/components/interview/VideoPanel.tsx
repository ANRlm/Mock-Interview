import { Camera, Focus, Headphones, Smile } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CAMERA_INSECURE_CONTEXT_ERROR, CAMERA_UNSUPPORTED_ERROR } from '@/hooks/useMediaPipe'

interface VideoPanelProps {
  ready: boolean
  eyeContactScore: number
  headPoseScore: number
  expression: string
  warning: string | null
}

const asPercent = (value: number) => `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`

const warningText = (warning: string | null): string | null => {
  if (!warning) {
    return null
  }
  if (warning === CAMERA_INSECURE_CONTEXT_ERROR) {
    return `当前页面不是安全上下文（HTTPS/localhost），浏览器会拦截摄像头权限。请改用 https://${window.location.host} 访问（同 IP），并在浏览器中信任证书。`
  }
  if (warning === CAMERA_UNSUPPORTED_ERROR) {
    return '当前浏览器不支持摄像头接口。'
  }
  return warning
}

export function VideoPanel({ ready, eyeContactScore, headPoseScore, expression, warning }: VideoPanelProps) {
  const warningLabel = warningText(warning)

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">摄像头预览</CardTitle>
        <Badge variant={ready ? 'success' : 'warning'}>{ready ? '实时检测中' : '等待授权'}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex aspect-video items-center justify-center rounded-lg border border-slate-800 bg-slate-950/80 text-slate-500">
          <div className="text-center">
            <Camera className="mx-auto mb-2" size={22} />
            <p className="text-xs">{ready ? '摄像头数据已接入 Phase4 行为分析' : '请允许摄像头权限以启用行为检测'}</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-md border border-slate-800 bg-slate-950/70 p-2">
            <p className="mb-1 flex items-center gap-1 text-[11px] text-slate-400">
              <Focus size={12} /> 注视
            </p>
            <p className="text-sm font-semibold text-slate-100">{asPercent(eyeContactScore)}</p>
          </div>
          <div className="rounded-md border border-slate-800 bg-slate-950/70 p-2">
            <p className="mb-1 flex items-center gap-1 text-[11px] text-slate-400">
              <Headphones size={12} /> 姿态
            </p>
            <p className="text-sm font-semibold text-slate-100">{asPercent(headPoseScore)}</p>
          </div>
          <div className="rounded-md border border-slate-800 bg-slate-950/70 p-2">
            <p className="mb-1 flex items-center gap-1 text-[11px] text-slate-400">
              <Smile size={12} /> 状态
            </p>
            <p className="text-sm font-semibold text-slate-100">{expression}</p>
          </div>
        </div>

        {warningLabel ? <p className="text-xs text-amber-300">{warningLabel}</p> : null}
      </CardContent>
    </Card>
  )
}

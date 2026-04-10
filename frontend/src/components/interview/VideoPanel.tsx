import { Camera } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function VideoPanel() {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">摄像头预览</CardTitle>
        <Badge variant="warning">Phase 4 启用</Badge>
      </CardHeader>
      <CardContent>
        <div className="flex aspect-video items-center justify-center rounded-lg border border-slate-800 bg-slate-950/80 text-slate-500">
          <div className="text-center">
            <Camera className="mx-auto mb-2" size={22} />
            <p className="text-xs">摄像头行为分析将在后续阶段接入</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

import { useMemo } from 'react'
import { useParams } from 'react-router-dom'

import { ReportPageView } from '@/components/report/ReportPage'
import { useInterviewStore } from '@/stores/interviewStore'

export function ReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const currentSession = useInterviewStore((state) => state.session)

  const resolvedSessionId = useMemo(() => {
    if (sessionId === 'latest') {
      return currentSession?.id ?? null
    }
    return sessionId ?? null
  }, [currentSession?.id, sessionId])

  if (!resolvedSessionId) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-sm text-slate-400">暂无可展示的报告，请先完成一次面试。</div>
    )
  }

  return <ReportPageView key={resolvedSessionId} sessionId={resolvedSessionId} />
}

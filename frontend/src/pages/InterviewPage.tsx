import { useParams } from 'react-router-dom'
import { InterviewRoom } from '@/components/interview/InterviewRoom'

export function InterviewPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  if (!sessionId) {
    return <div className="text-center text-text-muted">无效的会话</div>
  }

  return <InterviewRoom sessionId={sessionId} />
}
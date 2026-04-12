import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import { InterviewRoom } from '@/components/interview/InterviewRoom'
import { createSession, updateSession, uploadResume } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { useInterviewStore } from '@/stores/interviewStore'
import { useSettingsStore } from '@/stores/settingsStore'

export function InterviewPage() {
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const { selectedRole, subRole, resumeFile, setResumeFile } = useSettingsStore()
  const { session, setSession } = useInterviewStore()
  const creatingRef = useRef(false)

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (session || creatingRef.current) {
      return
    }

    creatingRef.current = true
    createSession({
      job_role: selectedRole,
      sub_role: subRole || undefined,
    })
      .then(async (created) => {
        if (resumeFile) {
          await uploadResume(created.id, resumeFile).catch(() => undefined)
        }
        const active = await updateSession(created.id, { status: 'active' })
        setSession(active)
        setResumeFile(null)
      })
      .finally(() => {
        creatingRef.current = false
      })
  }, [resumeFile, selectedRole, setResumeFile, setSession, session, subRole, isAuthenticated, navigate])

  if (!session) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-sm text-slate-400">正在初始化面试会话...</div>
    )
  }

  return <InterviewRoom />
}

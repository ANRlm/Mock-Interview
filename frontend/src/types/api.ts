import type { InterviewSession, JobRole } from './interview'

export interface CreateSessionPayload {
  job_role: JobRole
  sub_role?: string | null
}

export interface UpdateSessionPayload {
  status: InterviewSession['status']
}

export interface GenerateReportResponse {
  status: string
  session_id: string
}

export interface UploadResumeResponse {
  status: string
  path: string
}

export interface ResumeParsePayload {
  status?: string
  name?: string
  gender?: string
  major?: string
  education_level?: string
  self_introduction?: string
  summary?: string
  education?: string[]
  experience?: string[]
  projects?: string[]
  awards?: string[]
  target_position?: string
  skills?: string[]
  raw_summary?: string
  filename?: string
  bytes?: number
}

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

export type LLMProfileName = 'local' | 'cloud'

export interface LLMProfileOption {
  name: LLMProfileName
  label: string
  enabled: boolean
  default_model: string
  default_disable_thinking: boolean
  using_now: boolean
}

export interface LLMRuntimeActive {
  name: LLMProfileName
  label: string
  base_url: string
  model: string
  timeout_seconds: number
  disable_thinking: boolean
  enabled: boolean
}

export interface LLMProfilesResponse {
  active_profile: LLMProfileName
  active_model: string | null
  disable_thinking_override: boolean | null
  active_runtime: LLMRuntimeActive
  profiles: LLMProfileOption[]
}

export interface UpdateLLMRuntimePayload {
  profile: LLMProfileName
  model?: string | null
  disable_thinking?: boolean | null
}

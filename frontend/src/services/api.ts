import axios from 'axios'

import type {
  BehaviorBatchPayload,
  CreateSessionPayload,
  GenerateReportResponse,
  LLMProfilesResponse,
  ResumeParsePayload,
  UpdateLLMRuntimePayload,
  UpdateSessionPayload,
  UploadResumeResponse,
} from '@/types/api'
import type { ConversationMessage, InterviewReport, InterviewSession } from '@/types/interview'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 20000,
})

export async function createSession(payload: CreateSessionPayload): Promise<InterviewSession> {
  const { data } = await api.post<InterviewSession>('/sessions', payload)
  return data
}

export async function getSession(sessionId: string): Promise<InterviewSession> {
  const { data } = await api.get<InterviewSession>(`/sessions/${sessionId}`)
  return data
}

export async function updateSession(sessionId: string, payload: UpdateSessionPayload): Promise<InterviewSession> {
  const { data } = await api.patch<InterviewSession>(`/sessions/${sessionId}`, payload)
  return data
}

export async function getMessages(sessionId: string): Promise<ConversationMessage[]> {
  const { data } = await api.get<ConversationMessage[]>(`/sessions/${sessionId}/messages`)
  return data
}

export async function triggerReport(sessionId: string): Promise<GenerateReportResponse> {
  const { data } = await api.post<GenerateReportResponse>(`/sessions/${sessionId}/report`)
  return data
}

export async function getReport(sessionId: string): Promise<InterviewReport | null> {
  const response = await api.get<InterviewReport | { detail: string }>(`/sessions/${sessionId}/report`, {
    validateStatus: (status) => status === 200 || status === 202,
  })

  if (response.status === 202) {
    return null
  }

  return response.data as InterviewReport
}

export async function uploadResume(sessionId: string, file: File): Promise<UploadResumeResponse> {
  const form = new FormData()
  form.append('file', file)

  const { data } = await api.post<UploadResumeResponse>(`/sessions/${sessionId}/resume`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return data
}

export async function getResume(sessionId: string): Promise<ResumeParsePayload> {
  const { data } = await api.get<ResumeParsePayload>(`/sessions/${sessionId}/resume`)
  return data
}

export async function getLLMProfiles(): Promise<LLMProfilesResponse> {
  const { data } = await api.get<LLMProfilesResponse>('/llm/profiles')
  return data
}

export async function updateLLMRuntime(payload: UpdateLLMRuntimePayload): Promise<LLMProfilesResponse> {
  const { data } = await api.put<LLMProfilesResponse>('/llm/runtime', payload)
  return data
}

export async function postBehavior(sessionId: string, payload: BehaviorBatchPayload): Promise<{ status: string }> {
  const { data } = await api.post<{ status: string }>(`/sessions/${sessionId}/behavior`, payload)
  return data
}

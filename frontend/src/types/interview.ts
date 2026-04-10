export type JobRole = 'programmer' | 'lawyer' | 'doctor' | 'teacher'

export type SessionStatus = 'setup' | 'active' | 'completed'

export type MessageRole = 'interviewer' | 'candidate'

export type InputMode = 'voice' | 'text'

export interface InterviewSession {
  id: string
  job_role: JobRole
  sub_role: string | null
  status: SessionStatus
  started_at: string | null
  ended_at: string | null
  created_at: string
}

export interface ConversationMessage {
  id: string
  session_id: string
  role: MessageRole
  content: string
  timestamp: string
  turn_index: number
}

export interface InterviewReport {
  session_id: string
  llm_overall_score: number
  llm_professional_score: number
  llm_communication_score: number
  llm_logic_score: number
  llm_evaluation_text: string
  fluency_score: number
  behavior_score: number
  total_score: number
  strengths: string[]
  improvements: string[]
  behavior_detail?: {
    sample_count?: number
    emotion_distribution?: Record<string, number>
    attention_score?: number
    posture_score?: number
    engagement_score?: number
    gaze_stability?: number
    emotion_confidence?: number
    recommendations?: string[]
  }
  generated_at: string
}

export type InterviewStage = 'idle' | 'listening' | 'thinking' | 'speaking'

export type TtsProvider = 'cosyvoice2-http' | 'unknown'

export interface LlmTurnStats {
  backend: 'ollama-native' | 'openai-compatible' | 'cloud-openai-compatible'
  generated_chars: number
  total_seconds: number
  first_token_seconds?: number
  done_reason?: string
  prompt_tokens?: number
  generated_tokens?: number
  prompt_eval_seconds?: number
  generation_seconds?: number
  tokens_per_second?: number
  load_seconds?: number
  provider_total_seconds?: number
}

export type WsServerMessage =
  | { type: 'stt_partial'; text: string }
  | { type: 'stt_final'; text: string }
  | { type: 'llm_token'; token: string; response_id?: string }
  | { type: 'llm_done'; full_text: string; turn_index: number; response_id?: string }
  | ({ type: 'llm_stats' } & LlmTurnStats)
  | { type: 'tts_audio'; data: string; format: 'wav' | 'mp3'; provider?: TtsProvider; response_id?: string }
  | { type: 'tts_interrupted'; reason: string }
  | { type: 'tts_done'; response_id?: string }
  | { type: 'interview_end'; reason: string }
  | { type: 'error'; code: string; message: string }
  | { type: 'pong' }

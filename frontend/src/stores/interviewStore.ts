import { create } from 'zustand'

export type InterviewStage = 'idle' | 'listening' | 'thinking' | 'speaking'
export type InputMode = 'text' | 'voice'

export interface Message {
  id: string
  session_id: string
  role: 'candidate' | 'interviewer'
  content: string
  timestamp: string
  turn_index: number
}

export interface LLMStats {
  tokens_per_second?: number
  prompt_tokens?: number
  generated_tokens?: number
  first_token_seconds?: number
  total_seconds?: number
}

interface InterviewState {
  session: { id: string; job_role: string; sub_role?: string } | null
  setSession: (session: InterviewState['session']) => void
  messages: Message[]
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  stage: InterviewStage
  setStage: (stage: InterviewStage) => void
  inputMode: InputMode
  setInputMode: (mode: InputMode) => void
  streamText: string
  appendStreamToken: (token: string) => void
  clearStreamText: () => void
  sttPreview: string
  setSttPreview: (text: string) => void
  ttsProviderLabel: string
  setTtsProviderLabel: (label: string) => void
  llmStats: LLMStats | null
  setLlmStats: (stats: LLMStats | null) => void
  reset: () => void
}

export const useInterviewStore = create<InterviewState>((set) => ({
  session: null,
  setSession: (session) => set({ session }),
  messages: [],
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  stage: 'idle',
  setStage: (stage) => set({ stage }),
  inputMode: 'text',
  setInputMode: (inputMode) => set({ inputMode }),
  streamText: '',
  appendStreamToken: (token) =>
    set((state) => ({ streamText: state.streamText + token })),
  clearStreamText: () => set({ streamText: '' }),
  sttPreview: '',
  setSttPreview: (sttPreview) => set({ sttPreview }),
  ttsProviderLabel: '',
  setTtsProviderLabel: (ttsProviderLabel) => set({ ttsProviderLabel }),
  llmStats: null,
  setLlmStats: (llmStats) => set({ llmStats }),
  reset: () =>
    set({
      session: null,
      messages: [],
      stage: 'idle',
      inputMode: 'text',
      streamText: '',
      sttPreview: '',
      ttsProviderLabel: '',
      llmStats: null,
    }),
}))
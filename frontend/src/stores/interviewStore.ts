import { create } from 'zustand'

import type { ConversationMessage, InputMode, InterviewReport, InterviewSession, InterviewStage, LlmTurnStats, TtsProvider } from '@/types/interview'

interface InterviewState {
  session: InterviewSession | null
  messages: ConversationMessage[]
  stage: InterviewStage
  inputMode: InputMode
  sttPreview: string
  ttsProvider: TtsProvider
  ttsProviderLabel: string
  streamText: string
  llmStats: LlmTurnStats | null
  report: InterviewReport | null
  setSession: (session: InterviewSession | null) => void
  setMessages: (messages: ConversationMessage[]) => void
  addMessage: (message: ConversationMessage) => void
  setStage: (stage: InterviewStage) => void
  setInputMode: (mode: InputMode) => void
  setSttPreview: (text: string) => void
  setTtsProvider: (provider: TtsProvider) => void
  setTtsProviderLabel: (label: string) => void
  appendStreamToken: (token: string) => void
  clearStreamText: () => void
  setLlmStats: (stats: LlmTurnStats | null) => void
  setReport: (report: InterviewReport | null) => void
  reset: () => void
}

const initialState = {
  session: null,
  messages: [],
  stage: 'idle' as InterviewStage,
  inputMode: 'voice' as InputMode,
  sttPreview: '',
  ttsProvider: 'unknown' as TtsProvider,
  ttsProviderLabel: '未播放',
  streamText: '',
  llmStats: null,
  report: null,
}

export const useInterviewStore = create<InterviewState>((set) => ({
  ...initialState,
  setSession: (session) => set({ session }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setStage: (stage) => set({ stage }),
  setInputMode: (inputMode) => set({ inputMode }),
  setSttPreview: (sttPreview) => set({ sttPreview }),
  setTtsProvider: (ttsProvider) => set({ ttsProvider }),
  setTtsProviderLabel: (ttsProviderLabel) => set({ ttsProviderLabel }),
  appendStreamToken: (token) => set((state) => ({ streamText: `${state.streamText}${token}` })),
  clearStreamText: () => set({ streamText: '' }),
  setLlmStats: (llmStats) => set({ llmStats }),
  setReport: (report) => set({ report }),
  reset: () => set(initialState),
}))

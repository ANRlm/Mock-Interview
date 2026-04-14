import { create } from 'zustand'

export type SttStatus = 'idle' | 'connecting' | 'ready' | 'error'
export type TtsStatus = 'idle' | 'playing' | 'paused' | 'error'
export type LlmStatus = 'idle' | 'streaming' | 'done'

interface VoiceChannelState {
  sttStatus: SttStatus
  ttsStatus: TtsStatus
  llmStatus: LlmStatus
  setSttStatus: (status: SttStatus) => void
  setTtsStatus: (status: TtsStatus) => void
  setLlmStatus: (status: LlmStatus) => void
  resetAll: () => void
}

const initialState = {
  sttStatus: 'idle' as SttStatus,
  ttsStatus: 'idle' as TtsStatus,
  llmStatus: 'idle' as LlmStatus,
}

export const useVoiceChannelStore = create<VoiceChannelState>()((set) => ({
  ...initialState,

  setSttStatus: (sttStatus) => set({ sttStatus }),
  setTtsStatus: (ttsStatus) => set({ ttsStatus }),
  setLlmStatus: (llmStatus) => set({ llmStatus }),
  resetAll: () => set(initialState),
}))

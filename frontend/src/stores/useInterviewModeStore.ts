import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type InterviewMode = 'text' | 'voice'
export type ThemeMode = 'light' | 'dark' | 'system'

interface InterviewModeState {
  mode: InterviewMode
  theme: ThemeMode
  setMode: (mode: InterviewMode) => void
  setTheme: (theme: ThemeMode) => void
}

export const useInterviewModeStore = create<InterviewModeState>()(
  persist(
    (set) => ({
      mode: 'text',
      theme: 'system',

      setMode: (mode) => set({ mode }),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'interview-mode-storage',
      partialize: (state) => ({ mode: state.mode, theme: state.theme }),
    },
  ),
)

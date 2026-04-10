import { create } from 'zustand'

import type { LLMProfileName } from '@/types/api'
import type { JobRole } from '@/types/interview'

interface SettingsState {
  selectedRole: JobRole
  subRole: string
  resumeFile: File | null
  llmProfile: LLMProfileName
  llmModel: string
  llmDisableThinking: boolean
  setRole: (role: JobRole) => void
  setSubRole: (subRole: string) => void
  setResumeFile: (file: File | null) => void
  setLlmProfile: (profile: LLMProfileName) => void
  setLlmModel: (model: string) => void
  setLlmDisableThinking: (disabled: boolean) => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  selectedRole: 'programmer',
  subRole: '',
  resumeFile: null,
  llmProfile: 'local',
  llmModel: '',
  llmDisableThinking: true,
  setRole: (selectedRole) => set({ selectedRole }),
  setSubRole: (subRole) => set({ subRole }),
  setResumeFile: (resumeFile) => set({ resumeFile }),
  setLlmProfile: (llmProfile) => set({ llmProfile }),
  setLlmModel: (llmModel) => set({ llmModel }),
  setLlmDisableThinking: (llmDisableThinking) => set({ llmDisableThinking }),
}))

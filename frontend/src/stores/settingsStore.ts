import { create } from 'zustand'

import type { JobRole } from '@/types/interview'

interface SettingsState {
  selectedRole: JobRole
  subRole: string
  resumeFile: File | null
  setRole: (role: JobRole) => void
  setSubRole: (subRole: string) => void
  setResumeFile: (file: File | null) => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  selectedRole: 'programmer',
  subRole: '',
  resumeFile: null,
  setRole: (selectedRole) => set({ selectedRole }),
  setSubRole: (subRole) => set({ subRole }),
  setResumeFile: (resumeFile) => set({ resumeFile }),
}))

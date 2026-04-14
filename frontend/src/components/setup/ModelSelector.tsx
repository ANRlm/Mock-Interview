'use client'

import { ChevronDown } from 'lucide-react'

interface ModelSelectorProps {
  label: string
  value: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}

export function ModelSelector({ label, value, options, onChange }: ModelSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-text">{label}</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none bg-surface border border-border rounded-lg px-4 py-3 pr-10 text-text focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown
          size={18}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary pointer-events-none"
        />
      </div>
    </div>
  )
}

interface SpeedSliderProps {
  label: string
  value: number
  min?: number
  max?: number
  step?: number
  marks?: { value: number; label: string }[]
  onChange: (value: number) => void
}

export function SpeedSlider({ label, value, min = 0, max = 2, step = 1, marks, onChange }: SpeedSliderProps) {
  return (
    <div className="space-y-3">
      <div className="flex justify-between">
        <label className="text-sm font-medium text-text">{label}</label>
        <span className="text-sm text-text-secondary">
          {marks?.find((m) => m.value === value)?.label ?? value}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-surface rounded-full appearance-none cursor-pointer accent-primary"
      />
      {marks && (
        <div className="flex justify-between text-xs text-text-muted">
          {marks.map((mark) => (
            <span key={mark.value}>{mark.label}</span>
          ))}
        </div>
      )}
    </div>
  )
}

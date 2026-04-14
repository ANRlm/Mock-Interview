import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class', '[data-theme="dark"]'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'rgb(var(--geist-bg))',
        surface: 'rgb(var(--geist-surface))',
        text: 'rgb(var(--geist-text))',
        'text-secondary': 'rgb(var(--geist-text-secondary))',
        'text-muted': 'rgb(var(--geist-text-muted))',
        border: 'rgb(var(--geist-border))',
        primary: 'rgb(var(--geist-primary))',
        'primary-hover': 'rgb(var(--geist-primary-hover))',
      },
      fontFamily: {
        sans: ['Geist', 'IBM Plex Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'geist-sm': '0 1px 2px rgba(0, 0, 0, 0.05)',
        'geist-md': '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
        'geist-lg': '0 4px 6px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.06), 0 12px 24px rgba(0, 0, 0, 0.08)',
      },
      borderRadius: {
        DEFAULT: '6px',
        md: '8px',
        lg: '12px',
      },
      transitionDuration: {
        DEFAULT: '200ms',
      },
      transitionTimingFunction: {
        DEFAULT: 'ease-out',
      },
    },
  },
  plugins: [],
}

export default config
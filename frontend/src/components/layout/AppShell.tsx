import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { NavBar } from './NavBar'
import { useThemeStore } from '@/stores/useThemeStore'

export function AppShell({ children }: { children?: React.ReactNode }) {
  const { resolvedTheme } = useThemeStore()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolvedTheme)
  }, [resolvedTheme])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      const theme = useThemeStore.getState().theme
      if (theme === 'system') {
        const newResolved = mediaQuery.matches ? 'dark' : 'light'
        useThemeStore.setState({ resolvedTheme: newResolved })
        document.documentElement.setAttribute('data-theme', newResolved)
      }
    }
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return (
    <div className="min-h-screen bg-bg text-text">
      <NavBar />
      <main className="mx-auto w-full max-w-7xl px-4 py-8">
        {children ?? <Outlet />}
      </main>
    </div>
  )
}
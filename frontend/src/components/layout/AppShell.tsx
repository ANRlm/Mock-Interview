import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { NavBar } from './NavBar'
import { useThemeStore } from '@/stores/useThemeStore'

export function AppShell({ children }: { children?: React.ReactNode }) {
  const { resolvedTheme } = useThemeStore()

  useEffect(() => {
    const html = document.documentElement
    if (resolvedTheme === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }, [resolvedTheme])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      const theme = useThemeStore.getState().theme
      if (theme === 'system') {
        const newResolved = mediaQuery.matches ? 'dark' : 'light'
        useThemeStore.setState({ resolvedTheme: newResolved })
        const html = document.documentElement
        if (newResolved === 'dark') {
          html.classList.add('dark')
        } else {
          html.classList.remove('dark')
        }
      }
    }
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return (
    <div className="min-h-screen bg-bg text-text">
      <NavBar />
      <div className="w-full">
        {children ?? <Outlet />}
      </div>
    </div>
  )
}
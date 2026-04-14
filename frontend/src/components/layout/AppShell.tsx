import { useEffect } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/useThemeStore'

const navItems = [
  { to: '/', label: '首页' },
  { to: '/setup', label: '配置' },
  { to: '/interview', label: '面试' },
  { to: '/report/latest', label: '报告' },
]

export function AppShell() {
  const location = useLocation()
  const { isAuthenticated, user, logout } = useAuthStore()
  const { theme, resolvedTheme, setTheme } = useThemeStore()

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (theme === 'system') {
        const newResolved = mediaQuery.matches ? 'dark' : 'light'
        useThemeStore.setState({ resolvedTheme: newResolved })
        document.documentElement.setAttribute('data-theme', newResolved)
      }
    }
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [theme])

  const toggleTheme = () => {
    const next = resolvedTheme === 'dark' ? 'light' : 'dark'
    setTheme(next)
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 dark:bg-neutral-950 dark:text-neutral-100">
      <header className="sticky top-0 z-20 border-b border-neutral-800/80 bg-neutral-950/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-sm font-semibold tracking-wide text-neutral-100">
            Mock Interview
          </Link>
          <div className="flex items-center gap-3">
            <nav className="flex items-center gap-1 rounded-lg border border-neutral-800 bg-neutral-900/60 p-1">
              {navItems.map((item) => {
                const active =
                  item.to === '/' ? location.pathname === '/' : location.pathname === item.to || location.pathname.startsWith(`${item.to}/`)
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={cn(
                      'rounded-md px-3 py-1.5 text-xs transition-colors',
                      active ? 'bg-neutral-800 text-neutral-100' : 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200',
                    )}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={toggleTheme}>
              {resolvedTheme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </Button>
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-neutral-400">{user?.email}</span>
                <Button variant="ghost" size="sm" className="text-xs" onClick={logout}>
                  登出
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" className="text-xs" asChild>
                  <Link to="/login">登录</Link>
                </Button>
                <Button variant="outline" size="sm" className="text-xs" asChild>
                  <Link to="/register">注册</Link>
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}

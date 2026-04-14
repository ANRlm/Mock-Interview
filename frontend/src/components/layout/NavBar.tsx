import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { ThemeToggle } from './ThemeToggle'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '@/stores/authStore'

const navItems = [
  { to: '/', label: '首页' },
  { to: '/setup', label: '配置' },
  { to: '/interview', label: '面试' },
  { to: '/report/latest', label: '报告' },
]

export function NavBar() {
  const location = useLocation()
  const { isAuthenticated, user, logout } = useAuthStore()

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-bg/70 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-sm font-semibold tracking-wide text-text">
          Mock Interview
        </Link>

        <div className="flex items-center gap-3">
          <nav className="flex items-center gap-1 rounded-lg border border-border bg-surface p-1">
            {navItems.map((item) => {
              const active =
                item.to === '/'
                  ? location.pathname === '/'
                  : location.pathname.startsWith(item.to)
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={cn(
                    'rounded-md px-3 py-1.5 text-xs transition-colors',
                    active
                      ? 'bg-bg text-text'
                      : 'text-text-secondary hover:bg-bg hover:text-text'
                  )}
                >
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <ThemeToggle />

          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <Avatar initials={user.email[0].toUpperCase()} size="sm" />
              <Button variant="ghost" size="sm" className="text-xs" onClick={logout}>
                登出
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <Link to="/login">
                <Button variant="ghost" size="sm" className="text-xs">登录</Button>
              </Link>
              <Link to="/register">
                <Button variant="secondary" size="sm" className="text-xs">注册</Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
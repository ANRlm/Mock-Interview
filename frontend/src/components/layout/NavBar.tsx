import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { ThemeToggle } from './ThemeToggle'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '@/stores/authStore'

const navItems = [
  { to: '/', label: '首页' },
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

        <div className="flex items-center gap-6">
          <Link
            to={navItems[0].to}
            className={cn(
              'text-xs transition-colors',
              location.pathname === '/'
                ? 'text-text'
                : 'text-text-secondary hover:text-text'
            )}
          >
            {navItems[0].label}
          </Link>

          <Link to="/setup">
            <Button variant="primary" size="sm" className="text-xs">
              开始面试
            </Button>
          </Link>

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

            </div>
          )}
        </div>
      </div>
    </header>
  )
}
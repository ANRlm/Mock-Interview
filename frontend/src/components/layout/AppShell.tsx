import { Link, Outlet, useLocation } from 'react-router-dom'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/authStore'

const navItems = [
  { to: '/', label: '首页' },
  { to: '/setup', label: '配置' },
  { to: '/interview', label: '面试' },
  { to: '/report/latest', label: '报告' },
]

export function AppShell() {
  const location = useLocation()
  const { isAuthenticated, user, logout } = useAuthStore()

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_0%_0%,rgba(59,130,246,0.12),transparent_32%),radial-gradient(circle_at_100%_0%,rgba(14,165,233,0.1),transparent_28%),#05070d] text-slate-100">
      <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-sm font-semibold tracking-wide text-slate-100">
            Mock Interview
          </Link>
          <div className="flex items-center gap-3">
            <nav className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/60 p-1">
              {navItems.map((item) => {
                const active =
                  item.to === '/' ? location.pathname === '/' : location.pathname === item.to || location.pathname.startsWith(`${item.to}/`)
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={cn(
                      'rounded-md px-3 py-1.5 text-xs transition-colors',
                      active ? 'bg-blue-500/20 text-blue-200' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200',
                    )}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">{user?.email}</span>
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

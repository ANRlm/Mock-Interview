import { Moon, Sun } from 'lucide-react'
import { useThemeStore } from '@/stores/useThemeStore'
import { Button } from '@/components/ui/Button'

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useThemeStore()

  const toggle = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  return (
    <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={toggle}>
      {resolvedTheme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
    </Button>
  )
}
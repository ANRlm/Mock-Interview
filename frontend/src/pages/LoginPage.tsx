import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '@/stores/authStore'

export function LoginPage() {
  const navigate = useNavigate()
  const { login, register } = useAuthStore()
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isRegister) {
        await register(email, password)
        await login(email, password)
      } else {
        await login(email, password)
      }
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <h1 className="text-xl font-semibold text-text">
            {isRegister ? '注册账号' : '登录'}
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            {isRegister ? '创建新账号开始模拟面试' : '欢迎回来'}
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="email"
              placeholder="邮箱地址"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" loading={loading}>
              {isRegister ? '注册' : '登录'}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <button
              type="button"
              className="text-sm text-text-secondary hover:text-text"
              onClick={() => {
                setIsRegister(!isRegister)
                setError('')
              }}
            >
              {isRegister ? '已有账号？登录' : '没有账号？注册'}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
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

  const handleSwitchMode = () => {
    setIsRegister(!isRegister)
    setError('')
  }

  return (
    <div className="flex min-h-[70vh] items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      >
        <Card className="w-full max-w-md shadow-elevation-2">
          <CardHeader className="text-center pb-2">
            <motion.h1 
              className="text-heading-24 font-bold text-text"
              key={isRegister ? 'register' : 'login'}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            >
              {isRegister ? '创建账号' : '欢迎回来'}
            </motion.h1>
            <p className="mt-2 text-label-14 text-text-secondary">
              {isRegister ? '注册后即可开始 AI 模拟面试' : '登录以继续你的面试练习'}
            </p>
          </CardHeader>
          <CardContent className="space-y-5 pt-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-label-14 font-medium text-text">邮箱</label>
                <Input
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-label-14 font-medium text-text">密码</label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
              {error && (
                <motion.div 
                  className="py-2 px-3 rounded-md bg-error/10 border border-error/20"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  transition={{ duration: 0.2 }}
                >
                  <p className="text-label-14 text-error">{error}</p>
                </motion.div>
              )}
              <Button type="submit" className="w-full h-11" loading={loading}>
                {isRegister ? '注册' : '登录'}
              </Button>
            </form>
            
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-surface px-3 text-label-12 text-text-muted uppercase tracking-wider">或</span>
              </div>
            </div>
            
            <motion.button
              type="button"
              className="w-full py-3 px-4 rounded-md border border-border bg-transparent hover:bg-surface hover:border-border-hover transition-all duration-fast text-label-16 font-medium text-text"
              onClick={handleSwitchMode}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              transition={{ duration: 0.2 }}
            >
              {isRegister ? '已有账号？登录' : '没有账号？注册'}
            </motion.button>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

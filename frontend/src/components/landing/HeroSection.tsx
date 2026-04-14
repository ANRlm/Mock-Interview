'use client'

import { motion } from 'framer-motion'
import Lottie from 'lottie-react'
import { useEffect, useState } from 'react'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'

const ANIMATION_URL = 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json'

function AnimatedPlaceholder() {
  return (
    <div className="w-80 h-80 relative">
      <div className="absolute inset-0 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 animate-pulse" />
      <div className="absolute inset-8 rounded-full bg-gradient-to-br from-primary/10 to-transparent animate-pulse" />
    </div>
  )
}

function HeroAnimationInner() {
  const [animationData, setAnimationData] = useState<object | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    fetch(ANIMATION_URL)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch animation')
        return res.json()
      })
      .then((data) => {
        if (!cancelled) {
          setAnimationData(data)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  if (error || !animationData) {
    return <AnimatedPlaceholder />
  }

  return (
    <div className="w-80 h-80">
      <LottieAnimation animationData={animationData} />
    </div>
  )
}

function LottieAnimation({ animationData }: { animationData: object }) {
  return <Lottie loop autoplay animationData={animationData} />
}

function HeroAnimationWithError() {
  return (
    <ErrorBoundary fallback={<AnimatedPlaceholder />}>
      <HeroAnimationInner />
    </ErrorBoundary>
  )
}

const stats = [
  { value: '4+', label: '职位类型' },
  { value: '100%', label: '隐私保护' },
  { value: '实时', label: '反馈分析' },
]

export function HeroSection() {
  return (
    <section className="w-full min-h-screen bg-gradient-to-b from-neutral-50 to-white dark:from-neutral-950 dark:to-neutral-900 relative overflow-hidden">
      <motion.div
        className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px]"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      <motion.div
        className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-primary/5 rounded-full blur-[80px]"
        animate={{
          scale: [1.2, 1, 1.2],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      <motion.div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px]"
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      <div className="max-w-6xl mx-auto px-6 lg:px-8 py-20 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="text-center lg:text-left">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <span className="inline-block px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
                AI 驱动的面试练习平台
              </span>
            </motion.div>

            <motion.h1
              className="text-5xl lg:text-6xl font-bold tracking-tight mb-6 leading-tight"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <span className="text-text">模拟真实面试</span>
              <br />
              <span className="text-primary">提升你的表现</span>
            </motion.h1>

            <motion.p
              className="text-lg text-text-secondary mb-8 max-w-lg"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              与先进的 AI 面试官进行实时对话练习，获得即时反馈和专业建议。
            </motion.p>

            <motion.div
              className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              <motion.a
                href="/setup"
                className="inline-flex items-center justify-center px-10 py-4 rounded-xl bg-primary text-white text-lg font-medium hover:bg-primary-hover transition-colors"
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
              >
                开始面试
                <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </motion.a>

              <motion.a
                href="#features"
                className="inline-flex items-center justify-center px-10 py-4 rounded-xl border-2 border-border text-text text-lg font-medium hover:bg-surface transition-colors"
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
              >
                了解更多
              </motion.a>
            </motion.div>

            <motion.div
              className="mt-12 grid grid-cols-3 gap-6"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              {stats.map((stat, index) => (
                <div key={index} className="text-center lg:text-left">
                  <div className="text-2xl lg:text-3xl font-bold text-primary">{stat.value}</div>
                  <div className="text-sm text-text-muted">{stat.label}</div>
                </div>
              ))}
            </motion.div>
          </div>

          <motion.div
            className="flex justify-center"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <HeroAnimationWithError />
          </motion.div>
        </div>
      </div>

      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <svg className="w-6 h-6 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </motion.div>
    </section>
  )
}
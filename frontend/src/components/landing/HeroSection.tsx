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
  return <Lottie loop autoplay animationData={animationData} rendererSettings={{ preserveAspectRatio: 'xMidYMid slice' }} />
}

function HeroAnimationWithError() {
  return (
    <ErrorBoundary fallback={<AnimatedPlaceholder />}>
      <HeroAnimationInner />
    </ErrorBoundary>
  )
}

export function HeroSection() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-neutral-50 to-white dark:from-neutral-950 dark:to-neutral-900" />
      
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-primary/3 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-6xl mx-auto px-4 py-20 grid lg:grid-cols-2 gap-12 items-center">
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
            className="text-5xl lg:text-7xl font-bold tracking-tight mb-6"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <span className="text-text">模拟真实面试</span>
            <br />
            <span className="text-primary">提升你的表现</span>
          </motion.h1>

          <motion.p
            className="text-lg text-text-secondary max-w-xl mb-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            与 AI 面试官进行实时对话，获得即时反馈和专业建议。
            支持多种职位模拟，帮助你准备下一次重要面试。
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <motion.a
              href="/setup"
              className="inline-flex items-center justify-center px-8 py-3.5 rounded-lg bg-primary text-white font-medium hover:bg-primary-hover transition-colors"
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
              className="inline-flex items-center justify-center px-8 py-3.5 rounded-lg border border-border text-text font-medium hover:bg-surface transition-colors"
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              了解更多
            </motion.a>
          </motion.div>
        </div>

        <motion.div
          className="flex justify-center lg:justify-end"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <HeroAnimationWithError />
        </motion.div>
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
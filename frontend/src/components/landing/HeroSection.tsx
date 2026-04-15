'use client'

import { ArrowRight, ChevronDown, MessageSquare } from 'lucide-react'
import { motion } from 'framer-motion'

const stats = [
  { value: '4+', label: '职位类型' },
  { value: '100%', label: '隐私保护' },
  { value: '实时', label: '反馈分析' },
]

function FloatingMockup() {
  return (
    <div className="relative w-72 h-64">

      <motion.div
        className="absolute top-0 left-0 w-64 bg-surface border border-border rounded-lg shadow-elevation-2 p-4"
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
      >
  
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
            <MessageSquare className="w-3.5 h-3.5 text-primary" />
          </div>
          <div>
            <div className="text-label-14 font-medium text-text">AI 面试官</div>
            <div className="text-label-12 text-text-muted flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              在线
            </div>
          </div>
        </div>
        

        <div className="space-y-2">

          <div className="flex justify-end">
            <div className="max-w-[80%] px-2.5 py-1.5 rounded-lg rounded-br-sm bg-primary/10">
              <div className="text-label-12 text-text-muted">自我介绍</div>
            </div>
          </div>

          <div className="flex justify-start">
            <div className="max-w-[85%] px-2.5 py-1.5 rounded-lg rounded-bl-sm border border-border bg-bg">
              <div className="text-label-12 text-text-muted leading-relaxed">
                请介绍一下你自己，以及你对这个岗位的理解。
              </div>
            </div>
          </div>
        </div>
      </motion.div>


      <motion.div
        className="absolute bottom-0 right-0 w-48 bg-surface border border-border rounded-lg shadow-elevation-2 p-4"
        animate={{ y: [0, 6, 0] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
      >
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 rounded-full bg-primary" />
          <span className="text-label-14 text-text-muted">波形分析</span>
        </div>
        <div className="flex items-end gap-1 h-12">
          {[0.4, 0.7, 1, 0.8, 0.6, 0.9, 0.5, 0.75, 0.85, 0.65, 0.55, 0.7].map((h, i) => (
            <motion.div
              key={i}
              className="flex-1 bg-primary rounded-t"
              initial={{ height: '20%' }}
              animate={{ height: `${h * 100}%` }}
              transition={{ duration: 0.4, delay: i * 0.05, ease: 'easeOut' }}
            />
          ))}
        </div>
      </motion.div>
    </div>
  )
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
  }
}

const EASE_OUT = 'easeOut' as const

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: EASE_OUT }
  }
}

export function HeroSection() {
  return (
    <section className="w-full min-h-[60vh] bg-bg relative overflow-hidden">
      <div className="max-w-6xl mx-auto px-6 lg:px-8 py-12 relative z-10">
        <motion.div
          className="grid lg:grid-cols-2 gap-8 items-center"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="text-center lg:text-left">
            <motion.div variants={itemVariants}>
              <span className="inline-block px-4 py-1.5 rounded-full bg-surface border border-border text-text-secondary text-sm font-medium mb-6">
                AI 驱动的面试练习平台
              </span>
            </motion.div>

            <motion.h1
              className="text-heading-40 lg:text-heading-56 font-bold tracking-tight mb-6 leading-tight text-text"
              variants={itemVariants}
            >
              模拟真实面试
              <br />
              <span className="text-text">提升你的表现</span>
            </motion.h1>

            <motion.p
              className="text-copy-18 text-text-muted mb-8 max-w-lg"
              variants={itemVariants}
            >
              与先进的 AI 面试官进行实时对话练习，获得即时反馈和专业建议。
            </motion.p>

            <motion.div
              className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
              variants={itemVariants}
            >
              <motion.a
                href="/setup"
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-primary text-primary-foreground text-base font-medium"
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                transition={{ duration: 0.2 }}
              >
                开始面试
                <ArrowRight className="ml-2 w-5 h-5" />
              </motion.a>

              <motion.a
                href="#features"
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg border border-border bg-transparent text-text text-base font-medium hover:bg-surface hover:border-border-hover"
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                transition={{ duration: 0.2 }}
              >
                了解更多
              </motion.a>
            </motion.div>

            <motion.div
              className="mt-6 grid grid-cols-3 gap-6"
              variants={itemVariants}
            >
              {stats.map((stat, index) => (
                <div key={index} className="text-center lg:text-left">
                  <div className="text-heading-24 font-bold text-text">{stat.value}</div>
                  <div className="text-label-14 text-text-muted">{stat.label}</div>
                </div>
              ))}
            </motion.div>
          </div>

          <motion.div
            className="flex justify-center"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.3, ease: EASE_OUT }}
          >
            <FloatingMockup />
          </motion.div>
        </motion.div>
      </div>

      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      >
        <ChevronDown className="w-6 h-6 text-text-muted" />
      </motion.div>
    </section>
  )
}
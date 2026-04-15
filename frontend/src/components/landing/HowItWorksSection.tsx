'use client'

import { motion } from 'framer-motion'
import { FadeUp } from '@/components/ui/Motion'
import { Briefcase, Upload, Mic, FileText, TrendingUp } from 'lucide-react'

const steps = [
  {
    title: '选择职位',
    description: '选择你想要练习的职位类型',
    icon: Briefcase,
  },
  {
    title: '上传简历',
    description: '上传你的简历，AI 将据此定制问题',
    icon: Upload,
  },
  {
    title: '开始面试',
    description: '与 AI 面试官进行实时对话练习',
    icon: Mic,
  },
  {
    title: '获取报告',
    description: '面试结束后生成详细的能力分析报告',
    icon: FileText,
  },
  {
    title: '改进建议',
    description: '获得针对性的改进建议和能力提升方案',
    icon: TrendingUp,
  },
]

export function HowItWorksSection() {
  return (
    <section className="w-full py-16 bg-bg relative overflow-hidden">
      <div className="max-w-6xl mx-auto px-6">
        <FadeUp className="text-center mb-16">
          <h2 className="text-heading-32 font-semibold mb-3 text-text">如何使用</h2>
          <p className="text-copy-16 text-text-secondary max-w-2xl mx-auto">
            简单五步，开启你的 AI 面试练习之旅
          </p>
        </FadeUp>

        <div className="relative">
          <div className="hidden lg:block absolute top-7 left-0 right-0 h-px bg-border -translate-y-1/2" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-4">
            {steps.map((step, index) => {
              const Icon = step.icon
              return (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.15, duration: 0.2 }}
                  className="relative"
                >
                  <div className="flex flex-col items-center text-center">
                    <div className="relative z-10 w-14 h-14 rounded-full border border-border bg-bg flex items-center justify-center mb-4">
                      <Icon className="w-8 h-8 text-text-muted" strokeWidth={1.5} />
                    </div>
                    <h3 className="text-label-16 font-medium mb-1.5 text-text">{step.title}</h3>
                    <p className="text-copy-14 text-text-secondary">{step.description}</p>
                  </div>

                  {index < steps.length - 1 && (
                    <div className="hidden lg:block absolute top-7 left-full w-full h-px bg-border -translate-x-1/2" style={{ width: 'calc(100% - 2rem)' }} />
                  )}
                </motion.div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
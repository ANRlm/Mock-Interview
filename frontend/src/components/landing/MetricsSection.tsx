'use client'

import { motion } from 'framer-motion'
import { FadeUp } from '@/components/ui/Motion'

const metrics = [
  {
    label: 'LLM 首次响应',
    value: '~0.12秒',
    description: 'qwen3:8b 首 token 延迟 (RTX 5080)',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    color: 'text-amber-500 dark:text-amber-400',
    bgColor: 'bg-amber-500/10 dark:bg-amber-500/20',
  },
  {
    label: 'TTS 首次音频',
    value: '~2.5秒',
    description: 'CosyVoice2 流式首包延迟',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
      </svg>
    ),
    color: 'text-emerald-500 dark:text-emerald-400',
    bgColor: 'bg-emerald-500/10 dark:bg-emerald-500/20',
  },
  {
    label: '端到端延迟',
    value: '~4秒',
    description: '语音输入到 AI 语音输出的总延迟',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'text-blue-500 dark:text-blue-400',
    bgColor: 'bg-blue-500/10 dark:bg-blue-500/20',
  },
  {
    label: '成功率',
    value: '98%',
    description: '面试会话完成率',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'text-primary dark:text-primary',
    bgColor: 'bg-primary/10 dark:bg-primary/20',
  },
]

const progressItems = [
  { label: 'GPU 利用率', value: 91, color: 'bg-amber-500' },
  { label: 'STT 准确率', value: 95, color: 'bg-blue-500' },
  { label: 'TTS 流畅度', value: 90, color: 'bg-emerald-500' },
]

export function MetricsSection() {
  return (
    <section className="w-full py-24 bg-surface relative overflow-hidden">
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-primary/3 rounded-full blur-3xl" />

      <div className="max-w-5xl mx-auto px-6 relative z-10">
        <FadeUp className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">性能指标</h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            优化的系统性能，确保流畅的面试体验
          </p>
        </FadeUp>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {metrics.map((metric, index) => (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              className="p-6 rounded-2xl bg-bg border border-border hover:shadow-geist-lg transition-shadow"
            >
              <div className={`w-12 h-12 rounded-xl ${metric.bgColor} ${metric.color} flex items-center justify-center mb-4`}>
                {metric.icon}
              </div>
              <div className={`text-3xl font-bold ${metric.color} mb-1`}>
                {metric.value}
              </div>
              <div className="text-lg font-medium text-text mb-1">{metric.label}</div>
              <div className="text-sm text-text-muted">{metric.description}</div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="max-w-2xl mx-auto p-6 rounded-2xl bg-bg border border-border"
        >
          <h3 className="text-lg font-semibold mb-6 text-center">系统效率</h3>
          <div className="space-y-4">
            {progressItems.map((item, index) => (
              <div key={item.label}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-text-secondary">{item.label}</span>
                  <span className="text-sm font-medium text-text">{item.value}%</span>
                </div>
                <div className="h-2 bg-surface rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: `${item.value}%` }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.5 + index * 0.1, duration: 0.8, ease: 'easeOut' }}
                    className={`h-full ${item.color} rounded-full`}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
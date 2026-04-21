'use client'

import { motion } from 'framer-motion'
import { FadeUp } from '@/components/ui/Motion'
import { Zap, Volume2, Clock, CheckCircle } from 'lucide-react'

const metrics = [
  {
    label: 'LLM 首次响应',
    value: '~0.33秒',
    description: 'qwen3:8b 首 token 延迟',
    icon: Zap,
  },
  {
    label: 'TTS 首次音频',
    value: '~1.5-2.7秒',
    description: 'CosyVoice2 流式首包延迟',
    icon: Volume2,
  },
  {
    label: '端到端延迟',
    value: '~4秒',
    description: '语音输入到 AI 语音输出的总延迟',
    icon: Clock,
  },
  {
    label: '成功率',
    value: '98%',
    description: '面试会话完成率',
    icon: CheckCircle,
  },
]

const progressItems = [
  { label: 'STT 准确率', value: 95 },
  { label: 'TTS 流畅度', value: 90 },
]

export function MetricsSection() {
  return (
    <section className="w-full pt-20 pb-0 bg-surface">
      <div className="max-w-5xl mx-auto px-6">
        <FadeUp className="text-center mb-16">
          <h2 className="text-heading-32 font-semibold mb-3 text-text">性能指标</h2>
          <p className="text-copy-16 text-text-secondary max-w-2xl mx-auto">
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
              transition={{ delay: index * 0.1, duration: 0.4 }}
              className="p-6 rounded-lg border border-border bg-bg hover:border-border-hover transition-colors duration-fast"
            >
              <div className="w-12 h-12 rounded-xl bg-surface border border-border flex items-center justify-center mb-4">
                <metric.icon className="w-5 h-5 text-text-muted" strokeWidth={1.5} />
              </div>
              <div className="text-heading-24 font-semibold text-text mb-1">
                {metric.value}
              </div>
              <div className="text-label-16 font-medium text-text mb-1">{metric.label}</div>
              <div className="text-copy-14 text-text-muted">{metric.description}</div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4, duration: 0.4 }}
          className="max-w-2xl mx-auto p-6 rounded-lg border border-border bg-bg"
        >
          <h3 className="text-label-16 font-medium mb-6 text-center text-text">系统效率</h3>
          <div className="space-y-4">
            {progressItems.map((item, index) => (
              <div key={item.label}>
                <div className="flex justify-between mb-1.5">
                  <span className="text-copy-14 text-text-secondary">{item.label}</span>
                  <span className="text-copy-14 font-medium text-text">{item.value}%</span>
                </div>
                <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: `${item.value}%` }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.5 + index * 0.1, duration: 0.6, ease: 'easeOut' }}
                    className="h-full bg-text-muted rounded-full"
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
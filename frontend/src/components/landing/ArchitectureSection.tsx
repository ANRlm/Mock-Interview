'use client'

import { motion } from 'framer-motion'
import { FadeUp } from '@/components/ui/Motion'

const pipelineSteps = [
  {
    label: '用户语音',
    sublabel: 'Microphone Input',
    color: 'from-blue-500 to-blue-600',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
  },
  {
    label: 'FunASR STT',
    sublabel: 'Speech to Text',
    color: 'from-purple-500 to-purple-600',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
  },
  {
    label: 'qwen3:8b LLM',
    sublabel: 'AI Processing',
    color: 'from-amber-500 to-amber-600',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
  },
  {
    label: 'CosyVoice2 TTS',
    sublabel: 'Text to Speech',
    color: 'from-emerald-500 to-emerald-600',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
  },
  {
    label: '语音输出',
    sublabel: 'Audio Output',
    color: 'from-rose-500 to-rose-600',
    bgColor: 'bg-rose-500/10',
    borderColor: 'border-rose-500/30',
  },
]

function ArrowIcon() {
  return (
    <svg className="w-6 h-6 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
    </svg>
  )
}

function PipelineBox({ step, index }: { step: typeof pipelineSteps[0]; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className="relative flex flex-col items-center"
    >
      <div className={`px-6 py-4 rounded-xl ${step.bgColor} border ${step.borderColor} backdrop-blur-sm`}>
        <div className={`text-xl font-bold bg-gradient-to-r ${step.color} bg-clip-text text-transparent`}>
          {step.label}
        </div>
        <div className="text-xs text-text-muted mt-1">{step.sublabel}</div>
      </div>
    </motion.div>
  )
}

export function ArchitectureSection() {
  return (
    <section className="w-full py-24 bg-surface relative overflow-hidden">
      <div className="absolute inset-0 bg-grid-pattern opacity-5" />

      <div className="max-w-5xl mx-auto px-6">
        <FadeUp className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">技术架构</h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            实时语音面试管道：端到端延迟优化，支持本地 GPU 加速
          </p>
        </FadeUp>

        <div className="relative">
          <div className="hidden lg:flex items-center justify-between gap-2">
            {pipelineSteps.map((step, index) => (
              <div key={index} className="flex items-center">
                <PipelineBox step={step} index={index} />
                {index < pipelineSteps.length - 1 && (
                  <motion.div
                    initial={{ opacity: 0, scaleX: 0 }}
                    whileInView={{ opacity: 1, scaleX: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.3 + index * 0.1, duration: 0.4 }}
                    className="flex items-center px-2"
                  >
                    <ArrowIcon />
                  </motion.div>
                )}
              </div>
            ))}
          </div>

          <div className="lg:hidden space-y-4">
            {pipelineSteps.map((step, index) => (
              <div key={index} className="flex items-center gap-4">
                <PipelineBox step={step} index={index} />
                {index < pipelineSteps.length - 1 && (
                  <div className="flex justify-center">
                    <svg className="w-6 h-6 text-text-muted rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="mt-12 p-6 rounded-2xl bg-bg/50 border border-border backdrop-blur-sm"
          >
            <div className="grid md:grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-2xl font-bold text-primary mb-1">STT</div>
                <div className="text-sm text-text-secondary">FunASR 2-pass</div>
                <div className="text-xs text-text-muted mt-1">高准确度语音识别</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-amber-500 dark:text-amber-400 mb-1">LLM</div>
                <div className="text-sm text-text-secondary">qwen3:8b</div>
                <div className="text-xs text-text-muted mt-1">本地 GPU 推理</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-emerald-500 dark:text-emerald-400 mb-1">TTS</div>
                <div className="text-sm text-text-secondary">CosyVoice2</div>
                <div className="text-xs text-text-muted mt-1">低延迟语音合成</div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
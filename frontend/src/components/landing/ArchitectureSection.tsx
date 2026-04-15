'use client'

import { motion } from 'framer-motion'
import { FadeUp } from '@/components/ui/Motion'
import { ArrowRight } from 'lucide-react'

const pipelineSteps = [
  { label: '用户语音', sublabel: 'Microphone Input' },
  { label: 'FunASR STT', sublabel: 'Speech to Text' },
  { label: 'qwen3:8b LLM', sublabel: 'AI Processing' },
  { label: 'CosyVoice2 TTS', sublabel: 'Text to Speech' },
  { label: '语音输出', sublabel: 'Audio Output' },
]

function PipelineBox({ step, index }: { step: { label: string; sublabel: string }; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className="relative flex flex-col items-center"
    >
      <div className="px-5 py-3 rounded-lg border border-border bg-surface">
        <div className="text-label-16 font-medium text-text text-center">
          {step.label}
        </div>
        <div className="text-label-12 text-text-muted mt-0.5 text-center">{step.sublabel}</div>
      </div>
    </motion.div>
  )
}

export function ArchitectureSection() {
  return (
    <section className="w-full py-20 bg-surface">
      <div className="max-w-5xl mx-auto px-6">
        <FadeUp className="text-center mb-16">
          <h2 className="text-heading-32 font-semibold mb-3 text-text">技术架构</h2>
          <p className="text-copy-16 text-text-secondary max-w-2xl mx-auto">
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
                    <ArrowRight className="w-4 h-4 text-text-muted" />
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
                    <ArrowRight className="w-4 h-4 text-text-muted rotate-90" />
                  </div>
                )}
              </div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.6, duration: 0.4 }}
            className="mt-12 p-6 rounded-lg border border-border bg-bg"
          >
            <div className="grid md:grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-heading-24 font-semibold text-text mb-1">STT</div>
                <div className="text-label-14 text-text-secondary">FunASR 2-pass</div>
                <div className="text-label-12 text-text-muted mt-1">高准确度语音识别</div>
              </div>
              <div>
                <div className="text-heading-24 font-semibold text-text mb-1">LLM</div>
                <div className="text-label-14 text-text-secondary">qwen3:8b</div>
                <div className="text-label-12 text-text-muted mt-1">本地 GPU 推理</div>
              </div>
              <div>
                <div className="text-heading-24 font-semibold text-text mb-1">TTS</div>
                <div className="text-label-14 text-text-secondary">CosyVoice2</div>
                <div className="text-label-12 text-text-muted mt-1">低延迟语音合成</div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
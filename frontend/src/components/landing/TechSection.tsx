'use client'

import { motion } from 'framer-motion'
import { FadeUp, SlideInFromLeft, SlideInFromRight } from '@/components/ui/Motion'

const techStack = [
  { name: 'React', description: '现代化 UI 框架', icon: '⚛️' },
  { name: 'TypeScript', description: '类型安全', icon: '🔷' },
  { name: 'Tailwind CSS', description: '原子化样式', icon: '🎨' },
  { name: 'Framer Motion', description: '流畅动画', icon: '✨' },
]

const aiStack = [
  { name: 'FunASR', description: '语音识别', icon: '🎤' },
  { name: 'CosyVoice2', description: '语音合成', icon: '🔊' },
  { name: 'Ollama', description: '本地 LLM', icon: '🤖' },
]

export function TechSection() {
  return (
    <section className="py-24 bg-bg">
      <div className="max-w-6xl mx-auto px-4">
        <FadeUp className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">技术栈</h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            先进的技术带来极致的体验
          </p>
        </FadeUp>

        <div className="grid lg:grid-cols-2 gap-16">
          <SlideInFromLeft>
            <div className="space-y-6">
              <h3 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <span className="text-3xl">🛠️</span>
                前端技术
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {techStack.map((tech, index) => (
                  <motion.div
                    key={tech.name}
                    className="p-4 rounded-xl border border-border bg-surface hover:shadow-geist-md transition-shadow"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="text-3xl mb-2">{tech.icon}</div>
                    <h4 className="font-medium">{tech.name}</h4>
                    <p className="text-sm text-text-muted">{tech.description}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </SlideInFromLeft>

          <SlideInFromRight>
            <div className="space-y-6">
              <h3 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <span className="text-3xl">🤖</span>
                AI 能力
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {aiStack.map((tech, index) => (
                  <motion.div
                    key={tech.name}
                    className="p-4 rounded-xl border border-border bg-surface hover:shadow-geist-md transition-shadow"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="text-3xl mb-2">{tech.icon}</div>
                    <h4 className="font-medium">{tech.name}</h4>
                    <p className="text-sm text-text-muted">{tech.description}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </SlideInFromRight>
        </div>
      </div>
    </section>
  )
}
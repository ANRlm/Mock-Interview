'use client'

import { motion } from 'framer-motion'
import { FadeUp } from '@/components/ui/Motion'

const frontendStack = [
  { name: 'React 18.3', description: 'UI 框架', icon: '⚛️' },
  { name: 'TypeScript', description: '类型安全', icon: '🔷' },
  { name: 'Tailwind CSS', description: '样式框架', icon: '🎨' },
  { name: 'Framer Motion', description: '动画库', icon: '✨' },
  { name: 'Zustand', description: '状态管理', icon: '📦' },
  { name: 'React Router', description: '路由管理', icon: '🛣️' },
  { name: 'Radix UI', description: 'UI 组件', icon: '🧩' },
  { name: 'Lucide React', description: '图标库', icon: '💎' },
]

const backendStack = [
  { name: 'FastAPI', description: 'Web 框架', icon: '🚀' },
  { name: 'PostgreSQL', description: '数据库', icon: '🗄️' },
  { name: 'WebSocket', description: '实时通信', icon: '🔌' },
  { name: 'JWT Auth', description: '身份验证', icon: '🔐' },
]

const aiStack = [
  { name: 'FunASR', description: '语音识别(STT)', icon: '🎤' },
  { name: 'CosyVoice2', description: '语音合成(TTS)', icon: '🔊' },
  { name: 'Ollama', description: '本地 LLM 推理', icon: '🤖' },
  { name: 'qwen3:8b', description: '语言模型', icon: '🧠' },
]

const infraStack = [
  { name: 'Docker', description: '容器化', icon: '🐳' },
  { name: 'Vite', description: '构建工具', icon: '⚡' },
  { name: 'GPU Support', description: '硬件加速', icon: '🎮' },
  { name: 'Nginx', description: '反向代理', icon: '🌐' },
]

const categoryConfig = {
  frontend: { title: '前端技术', icon: '🛠️', color: 'from-blue-500 to-blue-600' },
  backend: { title: '后端服务', icon: '⚙️', color: 'from-emerald-500 to-emerald-600' },
  ai: { title: 'AI 能力', icon: '🤖', color: 'from-amber-500 to-amber-600' },
  infra: { title: '基础设施', icon: '🏗️', color: 'from-purple-500 to-purple-600' },
}

function TechCard({ tech, index }: { tech: { name: string; description: string; icon: string }; index: number }) {
  return (
    <motion.div
      className="p-4 rounded-xl border border-border bg-surface hover:shadow-geist-md transition-shadow"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
    >
      <div className="text-3xl mb-2">{tech.icon}</div>
      <h4 className="font-medium text-text">{tech.name}</h4>
      <p className="text-sm text-text-muted">{tech.description}</p>
    </motion.div>
  )
}

function TechCategory({
  title,
  icon,
  techs,
  color,
}: {
  title: string
  icon: string
  techs: typeof frontendStack
  color: string
}) {
  return (
    <FadeUp>
      <div className="space-y-6">
        <h3 className="text-2xl font-semibold mb-6 flex items-center gap-3">
          <span className="text-3xl">{icon}</span>
          <span className={`bg-gradient-to-r ${color} bg-clip-text text-transparent`}>{title}</span>
        </h3>
        <div className="grid grid-cols-2 gap-4">
          {techs.map((tech, index) => (
            <TechCard key={tech.name} tech={tech} index={index} />
          ))}
        </div>
      </div>
    </FadeUp>
  )
}

export function TechSection() {
  return (
    <section className="py-24 bg-bg">
      <div className="w-full px-4">
        <FadeUp className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">技术栈</h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            先进的技术带来极致的体验，20+ 技术组件构建完整系统
          </p>
        </FadeUp>

        <div className="grid lg:grid-cols-2 gap-12">
          <TechCategory
            title={categoryConfig.frontend.title}
            icon={categoryConfig.frontend.icon}
            techs={frontendStack}
            color={categoryConfig.frontend.color}
          />
          <TechCategory
            title={categoryConfig.backend.title}
            icon={categoryConfig.backend.icon}
            techs={backendStack}
            color={categoryConfig.backend.color}
          />
          <TechCategory
            title={categoryConfig.ai.title}
            icon={categoryConfig.ai.icon}
            techs={aiStack}
            color={categoryConfig.ai.color}
          />
          <TechCategory
            title={categoryConfig.infra.title}
            icon={categoryConfig.infra.icon}
            techs={infraStack}
            color={categoryConfig.infra.color}
          />
        </div>
      </div>
    </section>
  )
}
'use client'

import { motion } from 'framer-motion'
import { FadeUp } from '@/components/ui/Motion'
import {
  Monitor,
  Code2,
  Palette,
  Sparkles,
  Package,
  Route,
  Puzzle,
  Gem,
  Server,
  Database,
  Wifi,
  KeyRound,
  Mic2,
  Speaker,
  Bot,
  Brain,
  Container,
  Zap,
  Cpu,
  Globe,
} from 'lucide-react'

const frontendStack = [
  { name: 'React 18.3', description: 'UI 框架', icon: Monitor },
  { name: 'TypeScript', description: '类型安全', icon: Code2 },
  { name: 'Tailwind CSS', description: '样式框架', icon: Palette },
  { name: 'Framer Motion', description: '动画库', icon: Sparkles },
  { name: 'Zustand', description: '状态管理', icon: Package },
  { name: 'React Router', description: '路由管理', icon: Route },
  { name: 'Radix UI', description: 'UI 组件', icon: Puzzle },
  { name: 'Lucide React', description: '图标库', icon: Gem },
]

const backendStack = [
  { name: 'FastAPI', description: 'Web 框架', icon: Server },
  { name: 'PostgreSQL', description: '数据库', icon: Database },
  { name: 'WebSocket', description: '实时通信', icon: Wifi },
  { name: 'JWT Auth', description: '身份验证', icon: KeyRound },
]

const aiStack = [
  { name: 'FunASR', description: '语音识别(STT)', icon: Mic2 },
  { name: 'CosyVoice2', description: '语音合成(TTS)', icon: Speaker },
  { name: 'Ollama', description: '本地 LLM 推理', icon: Bot },
  { name: 'qwen3:8b', description: '语言模型', icon: Brain },
]

const infraStack = [
  { name: 'Docker', description: '容器化', icon: Container },
  { name: 'Vite', description: '构建工具', icon: Zap },
  { name: 'GPU Support', description: '硬件加速', icon: Cpu },
  { name: 'Nginx', description: '反向代理', icon: Globe },
]

function TechCard({ tech, index }: { tech: { name: string; description: string; icon: typeof Monitor }; index: number }) {
  const Icon = tech.icon
  return (
    <motion.div
      className="p-4 rounded-lg border border-border bg-bg hover:border-border-hover transition-colors duration-fast"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
    >
      <Icon className="w-5 h-5 text-text-muted mb-3" strokeWidth={1.5} />
      <h4 className="text-label-14 font-medium text-text">{tech.name}</h4>
      <p className="text-label-12 text-text-muted">{tech.description}</p>
    </motion.div>
  )
}

function TechCategory({ title, techs }: { title: string; techs: typeof frontendStack }) {
  return (
    <FadeUp>
      <div className="space-y-4">
        <h3 className="text-label-16 font-medium text-text">{title}</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
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
    <section className="w-full py-20 bg-bg">
      <div className="max-w-6xl mx-auto px-6">
        <FadeUp className="text-center mb-16">
          <h2 className="text-heading-32 font-semibold mb-3 text-text">技术栈</h2>
          <p className="text-copy-16 text-text-secondary max-w-2xl mx-auto">
            先进的技术带来极致的体验，多个技术组件构建完整系统
          </p>
        </FadeUp>

        <div className="grid lg:grid-cols-2 gap-12">
          <TechCategory title="前端技术" techs={frontendStack} />
          <TechCategory title="后端服务" techs={backendStack} />
          <TechCategory title="AI 能力" techs={aiStack} />
          <TechCategory title="基础设施" techs={infraStack} />
        </div>
      </div>
    </section>
  )
}
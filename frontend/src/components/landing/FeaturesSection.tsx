'use client'

import { ScaleIn, FadeUp, StaggerContainer, StaggerItem } from '@/components/ui/Motion'
import { MessageSquare, Zap, BarChart3, FileText, Mic, Shield } from 'lucide-react'

const features = [
  {
    icon: MessageSquare,
    title: 'AI 智能面试',
    description: '基于大语言模型，模拟真实面试官进行多轮对话',
  },
  {
    icon: Zap,
    title: '实时反馈',
    description: '面试过程中即时获得表现评估和改进建议',
  },
  {
    icon: BarChart3,
    title: '专业报告',
    description: '面试结束后生成详细的能力分析报告',
  },
  {
    icon: FileText,
    title: '简历分析',
    description: '上传简历，AI 根据你的背景定制面试问题',
  },
  {
    icon: Mic,
    title: '语音模式',
    description: '支持语音输入输出，体验真实面试场景',
  },
  {
    icon: Shield,
    title: '隐私保护',
    description: '所有对话本地处理，数据安全有保障',
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="w-full py-16 bg-surface">
      <div className="max-w-6xl mx-auto px-6">
        <FadeUp className="text-center mb-16">
          <h2 className="text-heading-32 font-semibold mb-3 text-text">为什么选择我们</h2>
          <p className="text-copy-16 text-text-secondary max-w-2xl mx-auto">
            专业的 AI 面试模拟平台，帮助你充分准备
          </p>
        </FadeUp>

        <StaggerContainer staggerDelay={0.1} className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <StaggerItem key={index}>
              <ScaleIn delay={index * 0.05}>
                <div className="rounded-lg border border-border bg-bg hover:border-border-hover transition-colors duration-fast p-6">
                  <div className="w-12 h-12 rounded-md bg-surface border border-border flex items-center justify-center mb-4">
                    <feature.icon className="w-8 h-8 text-text-muted" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-label-16 font-medium mb-2 text-text">{feature.title}</h3>
                  <p className="text-copy-14 text-text-secondary">{feature.description}</p>
                </div>
              </ScaleIn>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  )
}
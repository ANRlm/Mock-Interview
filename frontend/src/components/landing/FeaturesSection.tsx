'use client'

import { ScaleIn, FadeUp, StaggerContainer, StaggerItem } from '@/components/ui/Motion'

const features = [
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 2.5 0 1.561-1.278 2.733-2.512 2.733-1.514 0-2.614-.898-2.732-2.151L8 9.586a2.3 2.3 0 013.228 2.288v.001M12 21a9 9 0 100-18 9 9 0 000 18z" />
      </svg>
    ),
    title: 'AI 智能面试',
    description: '基于大语言模型，模拟真实面试官进行多轮对话',
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    title: '实时反馈',
    description: '面试过程中即时获得表现评估和改进建议',
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: '专业报告',
    description: '面试结束后生成详细的能力分析报告',
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
    title: '简历分析',
    description: '上传简历，AI 根据你的背景定制面试问题',
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    title: '语音模式',
    description: '支持语音输入输出，体验真实面试场景',
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    title: '隐私保护',
    description: '所有对话本地处理，数据安全有保障',
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-surface">
      <div className="max-w-6xl mx-auto px-4">
        <FadeUp className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">为什么选择我们</h2>
          <p className="text-text-secondary text-lg max-w-2xl mx-auto">
            专业的 AI 面试模拟平台，帮助你充分准备
          </p>
        </FadeUp>

        <StaggerContainer staggerDelay={0.1} className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <StaggerItem key={index}>
              <ScaleIn delay={index * 0.05}>
                <div className="p-6 rounded-xl border border-border bg-bg hover:shadow-geist-lg transition-shadow">
                  <div className="w-14 h-14 rounded-lg bg-primary/10 text-primary flex items-center justify-center mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-text-secondary">{feature.description}</p>
                </div>
              </ScaleIn>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  )
}
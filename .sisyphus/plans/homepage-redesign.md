# Homepage Redesign Plan

## Task
Redesign the homepage to be full-width and comprehensive, filling the entire viewport and showing detailed project tech stack.

## Current State
- HeroSection uses max-w-6xl (creates empty space on sides)
- TechSection only shows 7 tech items (4 frontend + 3 AI)
- Homepage only has 3 sections (Hero, Features, Tech)

## Target State
1. **HeroSection** - Full viewport width, animated background effects, larger CTA
2. **HowItWorksSection** - NEW: 5-step process with icons
3. **FeaturesSection** - Keep existing
4. **TechSection** - Expanded to 20+ items across 4 categories
5. **ArchitectureSection** - NEW: Pipeline diagram (STT→LLM→TTS)
6. **MetricsSection** - NEW: Performance metrics display
7. **HomePage** - Import all 6 sections

## Files to Create/Modify

### Create: HowItWorksSection.tsx
- 5 steps: 选择职位 → 上传简历 → 开始面试 → 获取报告 → 改进建议
- Horizontal on desktop, vertical on mobile
- Connecting lines between steps
- Icons for each step

### Create: ArchitectureSection.tsx
- Visual pipeline: [用户语音] → [FunASR STT] → [qwen3:8b LLM] → [CosyVoice2 TTS] → [语音输出]
- SVG arrows connecting boxes
- Technology labels

### Create: MetricsSection.tsx
- Performance cards showing:
  - LLM 首次响应: ~2.1秒
  - TTS 首次音频: ~3.5秒
  - 端到端延迟: ~3.5秒
  - 成功率: 100%
- Progress bars or metric cards

### Rewrite: HeroSection.tsx
- Remove max-w-6xl constraint
- Use min-h-screen
- Add animated gradient background
- Add floating blur circles
- Add grid pattern overlay
- Larger hero text
- Stats section (4+ 职位, 100% 隐私, 实时反馈)

### Rewrite: TechSection.tsx
4 categories with 4-8 items each:

**Frontend (8 items):**
- React 18.3 - UI框架
- TypeScript - 类型安全
- Tailwind CSS - 样式框架
- Framer Motion - 动画库
- Zustand - 状态管理
- React Router - 路由管理
- Radix UI - UI组件
- Lucide React - 图标库

**Backend (4 items):**
- FastAPI - Web框架
- PostgreSQL - 数据库
- WebSocket - 实时通信
- JWT Auth - 身份验证

**AI/LLM (4 items):**
- FunASR - 语音识别(STT)
- CosyVoice2 - 语音合成(TTS)
- Ollama - 本地LLM推理
- qwen3:8b - 语言模型

**Infrastructure (4 items):**
- Docker - 容器化
- Vite - 构建工具
- GPU Support - 硬件加速
- Nginx - 反向代理

### Update: HomePage.tsx
Add imports and render all sections:
```tsx
import { HeroSection } from '@/components/landing/HeroSection'
import { HowItWorksSection } from '@/components/landing/HowItWorksSection'
import { FeaturesSection } from '@/components/landing/FeaturesSection'
import { TechSection } from '@/components/landing/TechSection'
import { ArchitectureSection } from '@/components/landing/ArchitectureSection'
import { MetricsSection } from '@/components/landing/MetricsSection'

// Render in order:
<HeroSection />
<HowItWorksSection />
<FeaturesSection />
<TechSection />
<ArchitectureSection />
<MetricsSection />
```

## Design Requirements
- NO max-width constraints (except for readability in very long content)
- Use min-h-screen for hero
- Full viewport width (w-full)
- Animated backgrounds (gradients, blur circles, grid patterns)
- Use framer-motion for animations
- Use Tailwind CSS for styling
- Responsive design

## Acceptance Criteria
- [ ] HeroSection fills entire viewport width
- [ ] HeroSection has animated background effects
- [ ] HowItWorksSection shows 5 steps with icons
- [ ] TechSection shows 20+ technologies across 4 categories
- [ ] ArchitectureSection shows STT→LLM→TTS pipeline
- [ ] MetricsSection shows performance data
- [ ] Homepage renders all 6 sections
- [ ] No empty space on sides of any section
- [ ] Build passes

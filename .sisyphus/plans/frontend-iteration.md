# Plan: 前端页面全面优化

## TL;DR

> **Summary**: 修复前端多个 UI/UX 问题，包括暗色模式适配、状态管理 Bug、缺失组件、交互优化
> **Effort**: Medium-Large
> **Parallel**: YES - 多处独立修复可并行

## Context

用户要求无限制优化前端页面。通过代码审查发现以下问题类别：

1. **暗色模式适配** - Badge、ReportPage、MetricsSection、ArchitectureSection 使用硬编码颜色
2. **状态管理 Bug** - SetupPage resumeStatus 永不更新
3. **缺失组件/路由** - NavBar 指向不存在的 /register 页面
4. **UX 问题** - SetupPage 缺少角色选择 UI、API 错误静默失败

## Work Objectives

### Core Objective
修复所有发现的前端问题，提升用户体验和代码质量

### Must Have
- [ ] Badge 组件暗色模式适配
- [ ] ReportPage 颜色硬编码修复
- [ ] MetricsSection 颜色硬编码修复
- [ ] SetupPage resumeStatus 状态修复
- [ ] SetupPage 添加角色选择 UI
- [ ] NavBar 移除不存在的 /register 链接

### Should Have
- [ ] HomePage API 错误处理改进
- [ ] InterviewRoom 模式切换按钮语义修正
- [ ] ArchitectureSection 颜色硬编码修复

### Nice to Have
- [ ] HeroSection "开始面试" 按钮加载状态
- [ ] SetupPage LLM 配置显示优化

## Technical Decisions

| 问题 | 当前状态 | 修复方案 |
|------|---------|---------|
| Badge 暗色模式 | 使用 bg-green-100 等硬编码 | 添加 dark: 变体 |
| resumeStatus 状态 | useState('empty') 永不更新 | 添加上传成功后的状态更新 |
| SetupPage 角色选择 | 无 UI | 从 HomePage 的 roles 导入并显示 |
| NavBar /register 链接 | 链接存在但无路由 | 移除或改为 /login |
| ReportPage 颜色 | text-green-600 硬编码 | 使用 theme 颜色变量 |
| MetricsSection 颜色 | text-amber-500 硬编码 | 使用 theme 颜色变量 |
| HomePage API 错误 | .catch(() => {}) | Toast 或内联错误提示 |

## Verification Strategy

- 构建验证：`cd frontend && npm run build`
- 类型检查：`npm run lint`
- 功能验证：手动测试各页面交互

## TODOs

### Wave 1: Critical Fixes

- [ ] 1. 修复 Badge 组件暗色模式

  **What to do**: 修改 Badge.tsx，为 success/warning/error 变体添加 dark: 前缀的 Tailwind 类

  **References**:
  - File: `frontend/src/components/ui/Badge.tsx`

  **Acceptance Criteria**:
  - [ ] dark mode 下 Badge 颜色正确显示
  - [ ] light mode 保持不变

- [ ] 2. 修复 SetupPage resumeStatus 状态

  **What to do**: 
  - 添加上传成功后的状态更新逻辑
  - handleUploadResume 成功后 setResumeStatus('uploaded')

  **References**:
  - File: `frontend/src/pages/SetupPage.tsx`
  - Line: 16, 49-60

  **Acceptance Criteria**:
  - [ ] 上传成功后 Badge 显示"已解析"
  - [ ] 未上传时显示"待上传"

- [ ] 3. 移除 NavBar 无效的 /register 链接

  **What to do**: 删除 NavBar.tsx 第 56-58 行的 /register Link，因为 LoginPage 已内置注册切换

  **References**:
  - File: `frontend/src/components/layout/NavBar.tsx`

  **Acceptance Criteria**:
  - [ ] 导航栏只显示 /login 链接
  - [ ] 不再有 404 风险

### Wave 2: UI Improvements

- [ ] 4. SetupPage 添加角色选择 UI

  **What to do**: 
  - 从 HomePage 复制 roles 数组到 SetupPage
  - 添加卡片选择器 UI 让用户选择职位类型
  - 保持与 HomePage 一致的设计风格

  **References**:
  - Pattern: `frontend/src/pages/HomePage.tsx` (roles 数组)
  - Style: `frontend/src/components/landing/FeaturesSection.tsx` (卡片网格)

  **Acceptance Criteria**:
  - [ ] 用户可在 SetupPage 选择职位类型
  - [ ] 默认选中从 location.state 传入的角色

- [ ] 5. 修复 ReportPage 颜色硬编码

  **What to do**: 将 text-green-600/text-amber-600 替换为 theme 变量

  **References**:
  - File: `frontend/src/pages/ReportPage.tsx`
  - Lines: 131, 149

  **Acceptance Criteria**:
  - [ ] 优点/改进建议颜色在暗色模式下正确显示

- [ ] 6. 修复 MetricsSection 颜色硬编码

  **What to do**: 将 text-amber-500/text-emerald-500/text-blue-500 替换为 theme 变量

  **References**:
  - File: `frontend/src/components/landing/MetricsSection.tsx`
  - Lines: 16-17, 28-29, 40-41

  **Acceptance Criteria**:
  - [ ] 指标卡片颜色在暗色模式下正确显示

- [ ] 7. 修复 ArchitectureSection 颜色硬编码

  **What to do**: 将 text-amber-500/text-emerald-500 替换为 theme 变量

  **References**:
  - File: `frontend/src/components/landing/ArchitectureSection.tsx`
  - Lines: 133, 138

  **Acceptance Criteria**:
  - [ ] 架构图标签颜色在暗色模式下正确显示

### Wave 3: UX Enhancements

- [ ] 8. HomePage Sessions API 错误处理

  **What to do**: 添加错误状态和用户提示，而不是静默失败

  **References**:
  - File: `frontend/src/pages/HomePage.tsx`
  - Line: 34

  **Acceptance Criteria**:
  - [ ] API 失败时用户可见错误提示
  - [ ] 页面不会崩溃或显示异常状态

- [ ] 9. InterviewRoom 模式按钮语义修正

  **What to do**: 交换语音/文本按钮的图标和文案使其语义一致

  **References**:
  - File: `frontend/src/components/interview/InterviewRoom.tsx`
  - Lines: 224-228

  **Acceptance Criteria**:
  - [ ] "语音模式"按钮显示 Mic 图标
  - [ ] "文本模式"按钮显示 MicOff 图标

### Wave 4: Build Verification

- [ ] 10. 前端构建验证

  **What to do**: 运行 npm run build 确保无编译错误

  **References**:
  - Directory: `frontend/`

  **Acceptance Criteria**:
  - [ ] `npm run build` 成功
  - [ ] 无 TypeScript 错误
  - [ ] 无 lint 错误

## Dependencies

```
Wave 1 (Critical)
├── Badge 暗色模式修复
├── SetupPage resumeStatus 修复
└── NavBar /register 移除
    ↓
Wave 2 (UI Improvements)
├── SetupPage 角色选择 UI
├── ReportPage 颜色修复
├── MetricsSection 颜色修复
└── ArchitectureSection 颜色修复
    ↓
Wave 3 (UX Enhancements)
├── HomePage 错误处理
└── InterviewRoom 按钮语义
    ↓
Wave 4 (Verification)
└── Build verification
```

## Final Verification Wave

- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high
- [ ] F4. Scope Fidelity Check — deep

## Success Criteria

- 所有 Must Have 项完成
- npm run build 成功
- 无暗色模式颜色问题
- 无 404 路由风险

# AI 模拟面试 UI 重构实现计划

基于 `.omc/autopilot/spec.md` 规范，将当前界面重构为 Open Web UI 风格。

---

## 一、现状分析

### 当前结构
```
InterviewRoom (三栏布局)
├── InterviewSidebar (左侧 - 模式切换、结束面试)
├── 主内容区
│   ├── AudioPanel (语音模式 - 录音可视化)
│   ├── ChatPanel (文本模式 - 消息流)
│   └── 底部输入区
└── (StatusBar 已移除但逻辑存在)
```

### 已有的 Open Web UI 风格设计标记
- `design-tokens.css` 已定义 `gradient-primary`、`glass-bg`、`glow-primary` 等变量
- `Button` 组件已有 `gradient` 变体
- `Card` 组件已有 `glass` 属性支持
- `InterviewSidebar` 已实现可折叠侧边栏

---

## 二、文件变更清单

### Phase 1: 布局重构

#### 1.1 InterviewRoom.tsx
**变更类型**: 重构

**变更内容**:
- 将三栏布局改为双栏布局 (侧边栏 + 主内容)
- 侧边栏定位为导航/信息区，移至左侧固定位置
- 主内容区全屏显示聊天界面
- 移除内部的 AudioPanel/ChatPanel 条件渲染，改为统一聊天界面
- 语音模式时在聊天区域内显示音频可视化区域
- 添加顶部简化状态栏 (连接状态、职位信息)

**新结构**:
```
InterviewRoom
├── 顶部状态栏 (连接状态 | 职位信息 | 工具按钮)
├── 双栏布局
│   ├── InterviewSidebar (280px, 可折叠至 64px)
│   │   ├── Logo + 标题
│   │   ├── 连接状态
│   │   ├── 模式切换 (voice/text)
│   │   ├── 工具按钮组
│   │   └── 结束面试按钮
│   └── 主内容区
│       ├── 消息列表 (ChatPanel 增强版)
│       ├── 流式输出区域
│       └── 底部输入区
```

**关键代码位置**:
- 当前: `InterviewRoom.tsx:237-353` - 整个布局逻辑

---

#### 1.2 InterviewSidebar.tsx
**变更类型**: 增强

**变更内容**:
- 添加职位信息展示区域
- 添加工具按钮组 (重新生成问题、导出记录、设置)
- 优化折叠动画 (使用 spring easing)
- 添加深色模式玻璃态效果
- 添加面试进度指示器

**新增区域**:
```tsx
// 工具按钮组 (collapsed 时只显示图标)
const tools = [
  { icon: RefreshCw, label: '重新生成', action: 'regenerate' },
  { icon: Download, label: '导出记录', action: 'export' },
  { icon: Settings, label: '设置', action: 'settings' },
]
```

**关键代码位置**:
- 当前: `InterviewSidebar.tsx:1-191`

---

### Phase 2: 聊天界面增强

#### 2.1 ChatPanel.tsx
**变更类型**: 增强

**变更内容**:
- 优化空状态设计 - 使用更大的头像和更详细的文案
- 添加面试开始引导动画
- 消息时间戳显示 (每条消息)
- 消息复制/朗读按钮 (已有，需优化位置)
- 候选人消息使用浅色背景 (与 AI 消息区分)
- 流式输出添加打字机光标动画

**视觉更新**:
```tsx
// 候选人消息气泡 - 浅色主题
max-w-[85%] rounded-2xl px-4 py-3
bg-surface border border-border
text-text

// AI 消息气泡 - 深色/渐变主题 (保持)
max-w-[85%] rounded-2xl px-4 py-3
bg-gradient-to-br from-neutral-800 to-neutral-900
text-white border border-neutral-700/50
```

**关键代码位置**:
- 当前: `ChatPanel.tsx:30-92` - 消息渲染逻辑

---

#### 2.2 MessageBubble.tsx
**变更类型**: 增强

**变更内容**:
- 优化气泡圆角 (当前 18px，保持或略增)
- 添加消息时间戳显示
- 添加 "第 X 轮" 标记
- 朗读/复制按钮样式优化
- 添加翻译按钮 (预留)
- 候选人消息使用浅色主题
- AI 消息添加左侧渐变条装饰

**新样式**:
```tsx
// AI 消息样式增强
border-l-2 border-l-primary/50  // 左侧渐变条

// 候选人消息样式
bg-surface border-border  // 浅色主题
```

**关键代码位置**:
- 当前: `MessageBubble.tsx:42-96`

---

#### 2.3 TypingIndicator.tsx
**变更类型**: 优化

**变更内容**:
- thinking 状态: 保持三个点动画，但使用更柔和的渐变
- speaking 状态: 优化环形动画，使用 indigo/purple 渐变
- 统一背景样式，使用 glass-bg 和圆角

**关键代码位置**:
- 当前: `TypingIndicator.tsx:21-105`

---

### Phase 3: 音频可视化重构

#### 3.1 AudioPanel.tsx
**变更类型**: 重构

**变更内容**:
- 全屏音频可视化 (不局限于卡片)
- 录音时显示实时波形
- 添加玻璃态背景
- 添加光晕效果 (glowing effect)
- 显示音频状态文字 (等待录音、正在录音)

**新布局**:
```tsx
<div className="flex-1 flex flex-col items-center justify-center">
  {/* 大型环形音频可视化 */}
  <AudioRing size={200} level={level} active={active} />
  
  {/* 状态文字 */}
  <p className="mt-6 text-sm text-text-secondary">
    {active ? '正在录音...' : '点击开始录音'}
  </p>
  
  {/* 可选: 实时波形图 */}
  {active && <WaveformVisualizer level={level} />}
</div>
```

**关键代码位置**:
- 当前: `AudioPanel.tsx:9-21`

---

#### 3.2 AudioRing.tsx
**变更类型**: 增强

**变更内容**:
- 增大默认尺寸 (160 -> 200)
- 添加多层环形效果 (3-4 层)
- 添加动态光晕效果 (当 active 时)
- 优化颜色 (使用 indigo/purple 渐变)
- 添加呼吸动画 (pulse effect)
- 添加麦克风图标动画

**新环形层次**:
```tsx
// 从外到内
Layer 1: 外层光晕 (opacity: 0.1-0.2, blur: 30px)
Layer 2: 主环形 (border-width: 2px, gradient stroke)
Layer 3: 装饰环形 (border-width: 1px, opacity: 0.5)
Layer 4: 中心图标 (glass-bg, rounded-full)
```

**关键代码位置**:
- 当前: `AudioRing.tsx:13-86`

---

#### 3.3 AIVoiceAnimation.tsx (新增/重构)
**变更类型**: 重构

**变更内容**:
- 重命名为更通用的名称或合并到 AudioRing
- 作为 AI 状态指示器，显示 thinking/speaking
- speaking 时显示波形动画
- thinking 时显示脉冲动画

**关键代码位置**:
- 需查看当前 `AIVoiceAnimation.tsx` 完整内容

---

### Phase 4: UI 组件增强

#### 4.1 Button.tsx
**变更类型**: 小幅增强

**变更内容**:
- `gradient` 变体已存在，优化阴影效果
- 可选: 添加 `glow` 效果变体

**当前状态**: 基本满足需求，仅需微调

---

#### 4.2 Card.tsx
**变更类型**: 小幅增强

**变更内容**:
- `glass` 属性已支持
- 优化 `backdrop-blur` 强度

**当前状态**: 基本满足需求

---

#### 4.3 Textarea 组件
**变更类型**: 检查

**确认内容**:
- 是否需要增强 focus 效果
- 是否需要添加渐变边框

---

#### 4.4 新增组件

##### 4.4.1 StatusBadge.tsx (可选)
**用途**: 显示连接状态、录音状态等

```tsx
interface StatusBadgeProps {
  status: 'connected' | 'disconnected' | 'recording' | 'thinking' | 'speaking'
  label?: string
}
```

##### 4.4.2 ProgressIndicator.tsx (可选)
**用途**: 显示面试进度 (第几轮/总共)

```tsx
interface ProgressIndicatorProps {
  current: number
  total: number  // 可选，total 可能未知
}
```

---

### Phase 5: CSS/样式更新

#### 5.1 design-tokens.css
**变更类型**: 扩展

**新增变量**:
```css
/* 聊天相关 */
--chat-bubble-ai-bg: rgba(30, 30, 40, 0.9);
--chat-bubble-candidate-bg: var(--geist-surface);
--chat-bubble-radius: 18px;

/* 音频可视化 */
--audio-ring-primary: rgb(var(--gradient-start));
--audio-ring-secondary: rgb(var(--gradient-end));
--audio-glow: 0 0 30px rgba(var(--gradient-start), 0.4);

/* 动画 */
--animation-typewriter: 0.8s steps(20, end);
--animation-glow-pulse: 2s ease-in-out infinite;
```

**关键代码位置**:
- 当前: `design-tokens.css:123-168` - Open Web UI 风格部分

---

#### 5.2 index.css
**变更类型**: 检查

**确认内容**:
- Tailwind 配置是否支持所有新样式类
- 暗黑模式覆盖是否完整

---

### Phase 6: 状态管理

#### 6.1 interviewStore.ts
**变更类型**: 检查

**确认内容**:
- `stage` 状态: 'idle' | 'listening' | 'thinking' | 'speaking'
- `inputMode`: 'voice' | 'text'
- `llmStats`: 统计信息

---

## 三、实现顺序 (Phase by Phase)

### Phase 1: 布局重构 (预计 2-3 小时)
1. 读取 `StatusBar.tsx` 了解其功能
2. 重构 `InterviewRoom.tsx` 布局结构
3. 增强 `InterviewSidebar.tsx` 功能
4. 验证布局正常显示

### Phase 2: 聊天界面 (预计 2-3 小时)
1. 增强 `ChatPanel.tsx` 样式
2. 增强 `MessageBubble.tsx` 功能
3. 优化 `TypingIndicator.tsx` 动画
4. 验证消息显示正确

### Phase 3: 音频可视化 (预计 1-2 小时)
1. 增强 `AudioRing.tsx` 效果
2. 重构 `AudioPanel.tsx` 布局
3. 检查 `AIVoiceAnimation.tsx` 并决定合并或保留
4. 验证音频状态显示

### Phase 4: UI 组件与样式 (预计 1-2 小时)
1. 检查并增强 `Button.tsx` 和 `Card.tsx`
2. 扩展 `design-tokens.css` 变量
3. 检查 `index.css` 配置

### Phase 5: 集成测试 (预计 1-2 小时)
1. 全流程测试 (语音模式 + 文本模式)
2. 响应式布局测试
3. 主题切换测试 (如果实现)
4. 修复发现的问题

---

## 四、依赖关系

```
Phase 1 (布局)
    ↓ 依赖 InterviewSidebar 增强
Phase 2 (聊天界面)
    ↓ 独立
Phase 3 (音频可视化)
    ↓ 独立
Phase 4 (UI 组件)
    ↓ 为所有 phase 提供基础
Phase 5 (集成测试)
    ↓ 需要所有 phase 完成
```

**关键依赖**:
- `InterviewRoom.tsx` 依赖 `InterviewSidebar.tsx` 的增强功能
- `ChatPanel.tsx` 依赖 `MessageBubble.tsx` 的更新
- `AudioPanel.tsx` 依赖 `AudioRing.tsx` 的增强

---

## 五、风险与注意事项

### 风险
1. **布局重构可能影响现有功能** - 需要充分测试
2. **动画性能** - 多个动画同时运行可能影响性能
3. **响应式设计** - 需要在多种屏幕尺寸下测试

### 注意事项
1. 保持 `streamText` 功能正常 (打字机效果)
2. 保持 WebSocket 消息处理逻辑不变
3. 保持音频录制功能正常
4. 不要破坏现有的状态管理逻辑

---

## 六、测试清单

### 功能测试
- [ ] 语音模式录音功能
- [ ] 文本模式输入发送
- [ ] 消息流式输出
- [ ] 侧边栏折叠/展开
- [ ] 模式切换 (voice/text)

### 视觉测试
- [ ] 消息气泡样式正确
- [ ] 音频环形动画流畅
- [ ] 打字机效果正常
- [ ] 玻璃态效果显示
- [ ] 渐变显示正确

### 响应式测试
- [ ] 桌面端布局
- [ ] 平板端布局
- [ ] 移动端布局 (如果支持)

---

## 七、可选增强 (Spec 范围外)

如果时间允许，可以考虑:
1. 深色/浅色主题切换
2. 消息翻译功能
3. 面试进度指示器
4. Markdown 消息内容渲染
5. 快捷键支持
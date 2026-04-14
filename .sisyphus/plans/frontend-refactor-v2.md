# Mock Interview 前端彻底重构计划 (V2)

## TL;DR

> **Summary**: 从零开始重建前端，参考 Vercel/Geist 设计系统，极简现代风格，完美适配系统深浅色模式
> **Deliverables**: 全新前端 - 5 个页面、20+ 组件、完整 API 集成
> **Effort**: XL
> **Parallel**: YES - 3 waves
> **Critical Path**: Wave 1 (基础) → Wave 2 (核心) → Wave 3 (集成)

---

## Context

### 设计参考

**Vercel/Geist 设计系统核心规范：**

1. **色彩系统** (Geist Colors)
   - 10 色阶：Background, Gray, Blue, Red, Amber, Green, Teal, Purple, Pink
   - 双层背景：Background 1 (主背景) / Background 2 (卡片/表面)
   - 文本分层：Color 1–3 (正文/次要/弱化)
   - CSS 变量方案：`--geist-bg`, `--geist-surface`, `--geist-text`, `--geist-border`, `--geist-primary`
   - Light: `#fff` / `#f7f7f7` / `#111` / `#e5e7eb`
   - Dark: `#0b0b0f` / `#141414` / `#e5e7eb` / `#2d2d2d`

2. **字体系统** (Geist Typography)
   - Geist Sans (正文/标题) + Geist Mono (代码)
   - 字号层级：text-heading-72 → text-copy-16 等 Tailwind 兼容类名
   - 比例：4rem / 3rem / 2.25rem / 1.5rem / 1.25rem / 1rem / 0.875rem / 0.75rem

3. **间距与网格**
   - 4/8/12/16/20/24/32px 基准尺度
   - 响应式网格：grid-cols-1 → sm:grid-cols-2 → lg:grid-cols-4

4. **阴影层次**
   - Geist 使用分层阴影模拟环境光 + 直射光
   - shadow-geist-1, shadow-geist-2 层级

5. **动效原则**
   - CSS-first：opacity/transform 变化，避免 layout 动画
   - prefers-reduced-motion 优先
   - 200-300ms ease-out 标准过渡

6. **深浅色模式**
   - `data-theme="dark"` 切换，CSS 变量覆盖
   - `color-scheme: dark` 配合

---

## API 完整映射

### HTTP Endpoints

| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | /api/auth/register | ❌ | `{email, password}` | `{id, email}` |
| POST | /api/auth/login | ❌ | `{email, password}` | `{access_token, token_type, user}` |
| POST | /api/sessions | ✅ | `{job_role, sub_role?}` | `{id, job_role, status, ...}` |
| GET | /api/sessions/{id} | ✅ | - | SessionRead |
| PATCH | /api/sessions/{id} | ✅ | `{status}` | SessionRead |
| GET | /api/sessions/{id}/messages | ✅ | - | `Message[]` |
| POST | /api/sessions/{id}/resume | ✅ | multipart | `{status, path}` |
| GET | /api/sessions/{id}/resume | ✅ | - | parsed resume |
| POST | /api/sessions/{id}/report | ✅ | - | `{status, session_id}` |
| GET | /api/sessions/{id}/report | ✅ | - | ReportRead |
| GET | /api/llm/profiles | ✅ | - | profiles dict |
| PUT | /api/llm/runtime | ✅ | `{profile, model?, disable_thinking?, routing_strategy?}` | dict |

### WebSocket Endpoints

| Path | Auth | 用途 |
|------|------|------|
| /ws/interview/{session_id}?token=JWT | ✅ | 主面试流程 (LLM/STT/TTS/行为) |
| /ws/stt/{session_id}?token=JWT | ✅ | 独立 STT 通道 |
| /ws/tts/{session_id}?token=JWT | ✅ | 独立 TTS 通道 |

### WebSocket 消息协议

**Inbound:**
- `ping` → `pong`
- `candidate_message: {text}` → 触发 LLM 回复
- `audio_chunk: {data: base64, sample_rate?}` → 音频数据
- `audio_end` → 结束音频输入，触发 STT
- `interrupt` → 打断当前响应
- `behavior_frame: {frame_second, eye_contact_score, ...}` → 行为数据

**Outbound:**
- `llm_token: {token, response_id}` → LLM 流式输出
- `llm_done: {full_text, turn_index, response_id}` → LLM 完成
- `llm_stats: {...stats}` → LLM 统计
- `tts_audio: {data: base64, format, sample_rate, provider, response_id}` → TTS 音频
- `tts_done: {response_id}` → TTS 完成
- `tts_interrupted: {response_id}` → TTS 被打断
- `stt_partial: {text}` → STT 部分结果
- `stt_final: {text}` → STT 最终结果
- `behavior_warning: {warnings: [], frame_second}` → 行为警告
- `error: {...}` → 错误

---

## Work Objectives

### 交付物

1. **登录/注册页** - 极简表单，Geist 风格
2. **首页** - 角色选择 + 开始面试入口
3. **配置页** - 简历上传 + LLM 配置
4. **面试页** - 双模式 (Text/Voice) 实时面试界面
5. **报告页** - 面试报告展示 (图表 + 评分)

### Design System

- **Tailwind Config**: CSS 变量映射 Geist tokens
- **颜色**: `--geist-bg`, `--geist-surface`, `--geist-text`, `--geist-border`, `--geist-primary`
- **字体**: Geist Sans + Geist Mono
- **阴影**: 分层 shadow-geist-1/2
- **动效**: 200ms ease-out, prefers-reduced-motion 支持

---

## Execution Strategy

### Wave 1: 基础架构 (T1-T5)

| Task | 内容 |
|------|------|
| T1 | 项目结构重建 - src/ 目录、路由、布局组件 |
| T2 | Tailwind 配置 - Geist 颜色/字体/阴影 tokens |
| T3 | CSS 变量层 - 深浅色模式切换 |
| T4 | 基础组件 - Button, Input, Card, Badge |
| T5 | 布局组件 - AppShell, NavBar, ThemeToggle |

### Wave 2: 页面开发 (T6-T10)

| Task | 内容 |
|------|------|
| T6 | 登录/注册页 - AuthForm, JWT 存储 |
| T7 | 首页 - RoleSelector, SessionCard |
| T8 | 配置页 - ResumeUploader, LLMConfigPanel |
| T9 | 面试页 - InterviewRoom, ChatPanel, AudioPanel, StatusBar |
| T10 | 报告页 - ReportChart, ScoreCard, BehaviorAnalysis |

### Wave 3: 功能集成 (T11-T15)

| Task | 内容 |
|------|------|
| T11 | WebSocket 集成 - useInterview WS hook |
| T12 | Text-First Mode - 手动 TTS + 语音输入 |
| T13 | Voice-First Mode - 全双工 + 打断 |
| T14 | PiP 姿态检测 - PosePip 组件 |
| T15 | 集成测试 + git commit |

---

## TODOs

- [x] 1. 项目结构重建

  **What to do**:
  - 创建 `src/` 目录结构：
    - `src/pages/` - LoginPage, HomePage, SetupPage, InterviewPage, ReportPage
    - `src/components/layout/` - AppShell, NavBar, ThemeToggle
    - `src/components/ui/` - Button, Input, Card, Badge, Textarea
    - `src/components/interview/` - InterviewRoom, ChatPanel, AudioPanel, StatusBar, PosePip
    - `src/components/report/` - ReportChart, ScoreCard
    - `src/hooks/` - useAuth, useWebSocket, useMediaPipe, useAudioRecorder, useTTSPlayer
    - `src/stores/` - authStore, interviewStore, themeStore
    - `src/services/` - api.ts (HTTP client), websocket.ts
    - `src/lib/` - utils.ts, cn.ts
  - 创建 `src/App.tsx` - 路由配置 (React Router)
  - 创建 `src/main.tsx` - 入口
  - 创建 `src/vite-env.d.ts`

  **Must NOT do**:
  - 不参考任何旧组件样式
  - 不使用任何旧的颜色变量

  **References**:
  - Pattern: Vite + React + TypeScript 项目标准结构
  - Routing: React Router v6
  - State: Zustand

- [x] 2. Tailwind 配置

  **What to do**:
  ```typescript
  // tailwind.config.ts
  module.exports = {
    darkMode: ['class', '[data-theme="dark"]'],
    theme: {
      extend: {
        colors: {
          bg: 'rgb(var(--geist-bg))',
          surface: 'rgb(var(--geist-surface))',
          text: 'rgb(var(--geist-text))',
          'text-secondary': 'rgb(var(--geist-text-secondary))',
          'text-muted': 'rgb(var(--geist-text-muted))',
          border: 'rgb(var(--geist-border))',
          primary: 'rgb(var(--geist-primary))',
        },
        fontFamily: {
          sans: ['Geist', 'ui-sans-serif', 'system-ui', 'sans-serif'],
          mono: ['Geist Mono', 'SFMono-Regular', 'monospace'],
        },
        boxShadow: {
          'geist-sm': '0 1px 2px rgba(var(--shadow-color), 0.05)',
          'geist-md': '0 1px 3px rgba(var(--shadow-color), 0.1), 0 1px 2px rgba(var(--shadow-color), 0.06)',
          'geist-lg': '0 4px 6px rgba(var(--shadow-color), 0.05), 0 2px 4px rgba(var(--shadow-color), 0.06), 0 12px 24px rgba(var(--shadow-color), 0.08)',
        },
        borderRadius: {
          DEFAULT: '6px',
          md: '8px',
          lg: '12px',
        },
        transitionDuration: {
          DEFAULT: '200ms',
        },
        transitionTimingFunction: {
          DEFAULT: 'ease-out',
        },
      },
    },
  }
  ```

  **References**:
  - Geist Colors: https://vercel.com/geist/colors
  - Geist Typography: https://vercel.com/geist/typography

- [x] 3. CSS 变量层

  **What to do**:
  ```css
  /* src/index.css */
  @tailwind base;
  @tailwind components;
  @tailwind utilities;

  :root {
    color-scheme: light dark;
    --geist-bg: 255 255 255;
    --geist-surface: 249 249 249;
    --geist-text: 15 23 42;
    --geist-text-secondary: 71 85 105;
    --geist-text-muted: 148 163 184;
    --geist-border: 229 231 235;
    --geist-primary: 79 70 229;
    --geist-primary-hover: 99 102 241;
    --shadow-color: 0 0 0;
    font-family: 'Geist', 'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif;
  }

  [data-theme="dark"] {
    --geist-bg: 11 11 15;
    --geist-surface: 20 20 20;
    --geist-text: 229 231 235;
    --geist-text-secondary: 148 163 184;
    --geist-text-muted: 100 116 139;
    --geist-border: 45 45 45;
    --geist-primary: 147 197 253;
    --geist-primary-hover: 165 210 255;
    --shadow-color: 0 0 0;
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    background: rgb(var(--geist-bg));
    color: rgb(var(--geist-text));
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  ```

  **Must NOT do**:
  - 不使用任何 blue-500 / cyan-500 / purple-500
  - 不使用 bg-gradient

  **References**:
  - Geist Theme Switcher: https://vercel.com/geist/theme-switcher
  - Vercel Guidelines dark mode: https://vercel.com/design/guidelines

- [x] 4. 基础 UI 组件

  **What to do**:
  创建 `src/components/ui/`:
  - `Button.tsx` - variants: primary/secondary/ghost/destructive, sizes: sm/md/lg, loading state
  - `Input.tsx` - text input with Geist styling, error state
  - `Textarea.tsx` - multiline input
  - `Card.tsx` - surface container, optional header/footer
  - `Badge.tsx` - status labels, small pill
  - `Avatar.tsx` - user avatar placeholder
  - `Spinner.tsx` - loading indicator (CSS only, no emoji)

  所有组件：
  - 使用 CSS 变量，不硬编码颜色
  - 支持 dark mode (CSS 变量自动切换)
  - 支持 prefers-reduced-motion
  - 禁用状态有明确视觉提示

  **References**:
  - Geist Button: https://vercel.com/geist/button

- [x] 5. 布局组件

  **What to do**:
  创建 `src/components/layout/`:
  - `AppShell.tsx` - 根布局，ThemeProvider，Router outlet，NavBar
  - `NavBar.tsx` - 顶部导航：Logo + 路由链接 + 主题切换 + 用户菜单
  - `ThemeToggle.tsx` - 深浅色切换按钮 (Moon/Sun icon)
  - `useThemeStore.ts` - Zustand store 管理主题状态 + localStorage 持久化

  **References**:
  - Vercel Nav patterns

- [x] 6. 登录/注册页

  **What to do**:
  创建 `src/pages/LoginPage.tsx`:
  - 极简表单：email + password
  - 登录成功后存储 JWT → 重定向到首页
  - 错误状态显示 (401/422)
  - 注册切换 (登录/注册表单切换)

  创建 `src/stores/authStore.ts`:
  - `user`, `token`, `isAuthenticated`
  - `login(email, password)` → 调用 /api/auth/login
  - `register(email, password)` → 调用 /api/auth/register
  - `logout()` → 清除状态 + 重定向

  **References**:
  - Auth API: backend/app/api/auth.py

- [x] 7. 首页

  **What to do**:
  创建 `src/pages/HomePage.tsx`:
  - Hero 区域：大标题 + 描述
  - 角色选择卡片：Programmer / Lawyer / Doctor / Teacher
  - 已有的面试会话列表 (GET /api/sessions)
  - "开始新面试" 按钮 → 跳转 /setup

  创建 `src/components/home/RoleCard.tsx`:
  - 角色图标 + 名称 + 描述
  - 选中态 (border highlight)

  **References**:
  - Sessions API: backend/app/api/interview.py

- [x] 8. 配置页

  **What to do**:
  创建 `src/pages/SetupPage.tsx`:
  - 简历上传区 (拖拽 + 点击上传)
  - 已上传简历预览 (GET /api/sessions/{id}/resume)
  - LLM 配置面板 (GET /api/llm/profiles, PUT /api/llm/runtime)
  - "开始面试" 按钮 → POST /api/sessions → 跳转 /interview/{id}

  创建 `src/components/setup/ResumeUploader.tsx`:
  - 文件拖拽区
  - 上传进度
  - 解析结果展示

  创建 `src/components/setup/LLMConfigPanel.tsx`:
  - Profile 选择 (local/cloud)
  - Model 选择
  - Thinking 开关
  - 路由策略选择

  **References**:
  - Resume API: backend/app/api/resume.py
  - LLM Config API: backend/app/api/llm_config.py

- [x] 9. 面试页 (核心)

  **What to do**:
  创建 `src/pages/InterviewPage.tsx`:
  - 路由参数: /interview/:sessionId
  - 会话状态检查 (未登录 → /login)

  创建 `src/components/interview/InterviewRoom.tsx`:
  - 三栏布局 (桌面) / 单栏 (移动)
    - 左: AudioPanel (麦克风状态 + 波形)
    - 中: ChatPanel (消息流)
    - 右: StatusBar (阶段 + 统计)
  - 底部: 输入区 (Textarea + 发送按钮)
  - 右下: PosePip 浮窗
  - 顶部: 模式切换 (Text/Voice) + 结束按钮

  创建 `src/components/interview/ChatPanel.tsx`:
  - 消息列表 (用户/AI 分开)
  - 流式文本显示 (LLM token 实时渲染)
  - 每条 AI 消息旁: "朗读" 按钮 (Text-First 手动 TTS)
  - 时间戳 + 轮次显示

  创建 `src/components/interview/AudioPanel.tsx`:
  - 麦克风图标 (Mic/MicOff)
  - 音频波形可视化
  - 录音状态指示

  创建 `src/components/interview/StatusBar.tsx`:
  - 当前阶段: listening / thinking / speaking / idle
  - 连接状态
  - 轮次计数
  - STT 预览
  - LLM 统计 (tokens/sec)

  **References**:
  - WebSocket: backend/app/ws/interview_ws.py
  - Backend hooks: useWebSocket.ts pattern

- [x] 10. 报告页

  **What to do**:
  创建 `src/pages/ReportPage.tsx`:
  - 路由: /report/:sessionId

  创建 `src/components/report/ScoreCard.tsx`:
  - 总分大数字
  - 分项分数 (LLM综合 / 流畅度 / 行为)
  - 雷达图或柱状图

  创建 `src/components/report/BehaviorChart.tsx`:
  - 视线接触趋势
  - 头部姿态趋势
  - 表情分布

  创建 `src/components/report/EvaluationList.tsx`:
  - 优点列表
  - 改进建议

  **References**:
  - Report API: backend/app/api/report.py

- [x] 11. WebSocket Hook

  **What to do**:
  创建 `src/hooks/useInterviewWebSocket.ts`:
  - 连接 /ws/interview/{sessionId}?token={jwt}
  - 消息处理: llm_token → 追加显示, tts_audio → 播放音频, stt_final → 填入输入框
  - 发送: candidate_message, audio_chunk, audio_end, interrupt, behavior_frame
  - 自动重连
  - ping/pong 保持活跃

  创建 `src/hooks/useTTSPlayer.ts`:
  - 音频队列管理
  - base64 PCM → AudioContext 播放
  - 播放/暂停/打断

  创建 `src/hooks/useAudioRecorder.ts`:
  - MediaRecorder API
  - 音频 chunk 回调
  - VAD (语音活动检测) 支持

- [x] 12. Text-First Mode

  **What to do**:
  - LLM 回复后不自动 TTS，显示 "朗读" 按钮
  - 点击 "朗读" → 调用 TTS WebSocket 或 HTTP TTS
  - "语音输入" 按钮 → 录音 → STT → 填入 Textarea

  创建 `src/hooks/useManualVoiceInput.ts`:
  - start/stop recording
  - onTranscription callback

  创建 `src/hooks/useManualTTS.ts`:
  - play(text) → TTS 请求
  - stop()
  - status: idle/playing

- [x] 13. Voice-First Mode

  **What to do**:
  - 切换到 Voice 模式 → 连接独立 /ws/stt 和 /ws/tts
  - 麦克风自动录音 → STT → 发送 candidate_message
  - TTS 播放时自动静音麦克风
  - 随时可打断

  修改 `useAudioRecorder.ts`:
  - add mute/unmute functions
  - TTS 播放期间自动 mute

  修改 `InterviewRoom.tsx`:
  - 模式切换逻辑
  - Voice 模式: 隐藏 Textarea, 显示实时波形

- [x] 14. PiP 姿态检测

  **What to do**:
  创建 `src/components/interview/PosePip.tsx`:
  - 固定右下角，拖拽可移动
  - 显示摄像头画面 (MediaPipe 处理)
  - 姿态指标叠加显示
  - 最小化/展开切换
  - localStorage 记住位置

  创建 `src/hooks/useMediaPipe.ts`:
  - MediaPipe Face/Landmark/Pose 初始化
  - captureFrame() → 行为数据
  - cameraEnabled 状态

  **References**:
  - PosePip 原实现参考

- [x] 15. 集成测试 + Git Commit

  **What to do**:
  - TypeScript 类型检查: `npx tsc --noEmit --skipLibCheck`
  - 手动 smoke test: 登录 → 创建会话 → 简历上传 → 面试对话 → 查看报告
  - Git commit: `feat: complete frontend refactor with Vercel/Geist design system`
  - 清理旧文件 (如果还有残留)

---

## Final Verification Wave

- [x] F1. Plan Compliance Audit
- [x] F2. Code Quality Review
- [x] F3. Real Manual QA
- [x] F4. Scope Fidelity Check

---

## Design System Summary

### 颜色 (CSS Variables)

| Token | Light | Dark |
|-------|-------|------|
| `--geist-bg` | 255 255 255 | 11 11 15 |
| `--geist-surface` | 249 249 249 | 20 20 20 |
| `--geist-text` | 15 23 42 | 229 231 235 |
| `--geist-text-secondary` | 71 85 105 | 148 163 184 |
| `--geist-text-muted` | 148 163 184 | 100 116 139 |
| `--geist-border` | 229 231 235 | 45 45 45 |
| `--geist-primary` | 79 70 229 | 147 197 253 |
| `--geist-primary-hover` | 99 102 241 | 165 210 255 |

### 字体

- Sans: Geist, IBM Plex Sans, system-ui
- Mono: Geist Mono, SFMono-Regular

### 间距

- 4 / 8 / 12 / 16 / 20 / 24 / 32 / 48 / 64 px

### 圆角

- DEFAULT: 6px
- md: 8px
- lg: 12px

### 阴影

- `shadow-geist-sm`: 0 1px 2px rgba(0,0,0,0.05)
- `shadow-geist-md`: 0 1px 3px + 0 1px 2px
- `shadow-geist-lg`: 0 4px 6px + 0 2px 4px + 0 12px 24px

### 动效

- Duration: 200ms
- Timing: ease-out
- 支持 prefers-reduced-motion

---

## Success Criteria

1. ✅ 所有页面使用 Geist 设计语言
2. ✅ 深浅色模式完美切换 (无闪烁)
3. ✅ Text-First Mode: 手动 TTS + 语音输入
4. ✅ Voice-First Mode: 全双工 + 打断
5. ✅ PiP 姿态检测右下角浮动
6. ✅ TypeScript 类型检查通过
7. ✅ 集成测试通过

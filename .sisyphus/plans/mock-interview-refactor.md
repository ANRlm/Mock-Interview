# Mock Interview 彻底重构计划

## TL;DR
> **Summary**: 将现有半双工面试系统重构为双模式运行（Text-First + Voice-First），同时彻底重构前端 UI/UX。
> **Deliverables**:
> - Text-First Mode（默认）：LLM 纯文本输出 + 手动 TTS 触发 + 语音输入
> - Voice-First Mode（全双工）：分离 /ws/stt 和 /ws/tts 通道 + 真正双向打断
> - 全新 UI（Vercel 风格 + Monochrome + Dark/Light Mode）
> - 姿态检测 PiP 浮窗全局开启
> **Effort**: Large
> **Parallel**: YES - 3 waves
> **Critical Path**: Wave 1 (基础架构) → Wave 2 (核心功能) → Wave 3 (UI/集成)

## Context
### Original Request
用户要求彻底重构 Mock Interview 项目，包括双模式架构、前端 UI/UX 彻底重构、开发流程规范化。

### Interview Summary
已确认：
- **Text-First Mode**: LLM 仅输出纯文本 → 用户手动点击"朗读"触发 TTS；语音输入 → STT → 自动填充输入框 → 用户手动发送
- **Voice-First Mode**: 分离 WebSocket 通道（/ws/stt 和 /ws/tts）→ 真正全双工 → TTS 播放时静音麦克风
- **UI Layout**: 全新页面布局，简约/现代/高级，Vercel 风格，Monochrome
- **姿态检测**: PiP 浮窗（右下角可拖动）
- **提交规范**: 中文 + Conventional Commits

### Metis Review (gaps addressed)
- **Missed Questions**: MVP 边界、数据流同步、延迟目标、可靠性策略、API 版本管理
- **Guardrails**: 严格接口契约、分阶段交付、每个 deliverable 有可衡量成功标准
- **Scope Creep Risks**: UI 范围扩展、双模式复杂性、硬件假设
- **Unvalidated Assumptions**: 姿态检测 5s 间隔是否足够、Ollama streaming 稳定性、PiP UX
- **Missing Acceptance Criteria**: 需要为每个 deliverable 定义具体可测试的验收标准

## Work Objectives
### Core Objective
实现双模式面试系统 + 彻底重构前端 UI/UX

### Deliverables
1. **Text-First Mode** (默认)
   - LLM 仅输出纯文本（不自动 TTS）
   - 每条回复旁有"朗读"按钮（手动触发 TTS）
   - 输入框旁有"语音输入"按钮（STT → 填充输入框）

2. **Voice-First Mode** (全双工)
   - 分离 /ws/stt（STT 上游）和 /ws/tts（TTS 下游）WebSocket 通道
   - 用户可随时打断 AI 说话
   - TTS 播放时静音麦克风

3. **前端 UI/UX 彻底重构**
   - Vercel 风格设计语言
   - Monochrome 色彩（极致黑白）
   - Dark/Light Mode 完美支持

4. **姿态检测全局开启**
   - PiP 浮窗（右下角可拖动）

### Definition of Done (verifiable conditions with commands)
- [ ] Text-First: 发送文本 → LLM streaming → 显示纯文本 → 点击"朗读" → TTS 播放
- [ ] Text-First: 点击语音输入 → 录音 → 松开 → STT → 文字填充输入框
- [ ] Voice-First: 建立 /ws/stt 和 /ws/tts 连接 → 语音输入 → LLM 响应 → TTS 流式输出 → 可随时打断
- [ ] Voice-First: TTS 播放期间麦克风自动静音
- [ ] UI: 访问 /interview → 全新布局（无原有样式包袱）
- [ ] UI: 切换 Dark/Light Mode → 完美适配
- [ ] Pose: 姿态检测 PiP 浮窗显示在右下角，可拖动
- [ ] Pose: 无论 Text-First 还是 Voice-First，姿态检测均全局开启

### Must Have
- Text-First Mode 功能完整可用
- Voice-First Mode 全双工通信（分离通道 + 打断）
- 全新 Vercel 风格 UI（Monochrome）
- Dark/Light Mode 支持
- 姿态检测 PiP 全局开启
- 每个阶段测试通过后提交 git push

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- 不得保留原有 Slate/Purple 蓝色调 UI
- 不得在新 UI 中使用 gradient backgrounds
- 不得在 Voice-First Mode 下显示文字对话区
- 不得在 Text-First Mode 自动播放 TTS
- 不得移除姿态检测功能
- 不得改动后端认证逻辑（JWT）

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after + 手动冒烟测试
- QA policy: 每个 task 包含 happy path + failure scenarios
- Evidence: .sisyphus/evidence/task-{N}-{slug}.{ext}

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave = under-splitting.

**Wave 1: 基础架构**
- T1: 后端 - 分离音频通道 WebSocket 端点
- T2: 前端 - 状态管理重构（Zustand 双模式 store）
- T3: 前端 - CSS 设计系统（Monochrome + Vercel）
- T4: 前端 - PiP 姿态检测组件

**Wave 2: 核心功能**
- T5: Text-First Mode - 消息显示 + 手动 TTS
- T6: Text-First Mode - 语音输入 → STT → 填充
- T7: Voice-First Mode - 全双工通信（并发 STT + TTS）
- T8: Voice-First Mode - 打断机制 + 麦克风静音

**Wave 3: UI/集成 + 收尾**
- T9: 页面布局重构（全新 InterviewRoom）
- T10: Dark/Light Mode 完美适配
- T11: 集成测试 + 冒烟测试
- T12: README 更新 + git commit

### Dependency Matrix
```
T1 (WS 分离) ← 无依赖
T2 (Zustand) ← 无依赖
T3 (CSS) ← 无依赖
T4 (PiP) ← T3 (CSS 设计系统)
T5 (Text Msg+TTS) ← T2 (状态管理)
T6 (Voice Input) ← T2, T5
T7 (Full Duplex) ← T1, T2
T8 (Interrupt+Mute) ← T1, T7
T9 (Layout) ← T3, T4, T5, T6, T7, T8
T10 (Theme) ← T3, T9
T11 (集成测试) ← T5, T6, T7, T8, T9, T10
T12 (README+Commit) ← T11
```

### Agent Dispatch Summary
- Wave 1: 4 个并行任务 → 4 个 build agents
- Wave 2: 4 个并行任务 → 4 个 build agents（部分依赖 Wave 1）
- Wave 3: 4 个并行任务 → 4 个 build agents

## TODOs

- [ ] 1. 后端 - 分离音频通道 WebSocket 端点

  **What to do**: 在 `backend/app/ws/` 下创建两个新的 WebSocket 端点：
  - `/ws/stt` - STT 上游：接收用户音频 chunks，转发给 FunASR，返回识别结果
  - `/ws/tts` - TTS 下游：接收 LLM token，触发 TTS 合成，发送 PCM audio chunks
  修改 `interview_ws.py` 的 SessionRuntime 支持多通道并发。

  **Must NOT do**: 不改动现有 /ws/interview 端点（保持 Text-First 兼容）；不动认证逻辑

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: 涉及 WebSocket 并发、多个服务协调
  - Skills: [] - 通用后端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 1 | Blocks: T7, T8 | Blocked By: none

  **References**:
  - Pattern: `backend/app/ws/interview_ws.py:107-250` - WebSocket 端点模式
  - API/Type: `backend/app/services/stt_service.py:transcribe_stream_events` - STT streaming
  - API/Type: `backend/app/services/tts_service.py:stream_synthesize` - TTS streaming
  - External: Ollama streaming API - /api/chat with stream:true

  **Acceptance Criteria**:
  - [ ] `/ws/stt/{session_id}` 端点可接收 audio_chunk 并返回 stt_partial/final
  - [ ] `/ws/tts/{session_id}` 端点可接收 text 并返回 tts_audio chunks
  - [ ] 两个新端点均通过 JWT 认证
  - [ ] 并发测试：STT 和 TTS 可同时运行不冲突

  **QA Scenarios**:
  ```
  Scenario: STT WebSocket 正常流式识别
    Tool: Bash
    Steps: |
      # 连接 STT 端点
      wscat -c ws://localhost:8000/ws/stt/{session_id}?token={jwt}
      # 发送测试音频
      echo '{"type":"audio_chunk","data":"base64_pcm","sample_rate":16000}' | wscat -c ...
    Expected: 收到 stt_partial 和 stt_final 消息
    Evidence: .sisyphus/evidence/task-1-stt-ws.{ext}

  Scenario: TTS WebSocket 正常流式合成
    Tool: Bash
    Steps: |
      # 连接 TTS 端点
      wscat -c ws://localhost:8000/ws/tts/{session_id}?token={jwt}
      # 发送文本
      echo '{"type":"text_input","text":"测试文本","response_id":"test-123"}' | wscat -c ...
    Expected: 收到 tts_audio chunks (pcm_s16le)
    Evidence: .sisyphus/evidence/task-1-tts-ws.{ext}

  Scenario: 未认证访问被拒绝
    Tool: Bash
    Steps: |
      wscat -c ws://localhost:8000/ws/stt/test-session  # 无 token
    Expected: 连接被关闭，返回 4401
    Evidence: .sisyphus/evidence/task-1-stt-auth-fail.{ext}
  ```

  **Commit**: YES | Message: `feat(backend): 新增分离的 STT/TTS WebSocket 通道` | Files: `backend/app/ws/stt_ws.py, backend/app/ws/tts_ws.py`

- [ ] 2. 前端 - Zustand 双模式状态管理

  **What to do**: 重构前端状态管理：
  - 创建 `useInterviewModeStore`（Zustand）：管理 `mode: 'text' | 'voice'`、各通道状态
  - 创建 `useVoiceChannelStore`：管理 STT/TTS/LLM streaming 状态
  - 保留 `useInterviewStore` 用于会话数据
  - 更新 types/interview.ts 添加新类型

  **Must NOT do**: 不改动现有 interviewStore 的会话数据逻辑；不动 API 调用

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 状态管理设计
  - Skills: [] - 前端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 1 | Blocks: T5, T6, T7 | Blocked By: none

  **References**:
  - Pattern: `frontend/src/stores/interviewStore.ts` - 现有 Zustand store 模式
  - API/Type: `frontend/src/types/interview.ts:InputMode` - 当前 InputMode 类型
  - Test: `frontend/src/stores/__tests__/` - 如存在则参考测试模式

  **Acceptance Criteria**:
  - [ ] `useInterviewModeStore` 包含 `mode: 'text' | 'voice'` 状态
  - [ ] `useVoiceChannelStore` 包含 `sttStatus, ttsStatus, llmStatus` 状态
  - [ ] `setMode()` 方法正确切换模式并触发相关清理
  - [ ] Dark/Light mode 偏好持久化到 localStorage

  **QA Scenarios**:
  ```
  Scenario: Text-First Mode 状态正确
    Tool: interactive_bash
    Steps: |
      启动前端 dev server
      打开浏览器控制台
      执行: window.__store.getState()
    Expected: mode === 'text', sttStatus === 'idle', ttsStatus === 'idle'

  Scenario: Voice-First Mode 状态正确
    Tool: interactive_bash
    Steps: |
      切换到 Voice-First Mode
      检查状态: window.__store.getState()
    Expected: mode === 'voice', sttStatus === 'ready', ttsStatus === 'ready'

  Scenario: 模式切换清理状态
    Tool: interactive_bash
    Steps: |
      Voice-First 下建立连接
      切换到 Text-First
    Expected: sttStatus/ttsStatus 重置为 idle，连接已关闭
    Evidence: .sisyphus/evidence/task-2-mode-switch.{ext}
  ```

  **Commit**: YES | Message: `feat(frontend): 重构 Zustand 双模式状态管理` | Files: `frontend/src/stores/useInterviewModeStore.ts, frontend/src/stores/useVoiceChannelStore.ts`

- [ ] 3. 前端 - CSS 设计系统（Monochrome + Vercel）

  **What to do**: 从零设计 CSS 设计系统：
  - Tailwind config：Monochrome 色彩（black/white/gray only）
  - CSS Variables：支持 Dark/Light mode
  - 基础组件样式：Button, Input, Card, Textarea（无原有蓝色调）
  - Vercel 风格排版：font-family, font-weight, letter-spacing
  - 移除所有 gradient backgrounds

  **Must NOT do**: 不使用 blue-/purple-/cyan- 等彩色 Tailwind 类；不动功能逻辑

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: UI 设计
  - Skills: [] - 前端样式任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 1 | Blocks: T4, T9, T10 | Blocked By: none

  **References**:
  - Pattern: `frontend/tailwind.config.ts` - 现有 Tailwind 配置
  - Pattern: `frontend/src/components/ui/button.tsx` - 现有 Button 样式
  - External: Vercel 官网 - 设计风格参考

  **Acceptance Criteria**:
  - [ ] Tailwind config 包含 Monochrome 色彩体系
  - [ ] CSS Variables 支持 `dark:` 和 `light:` 主题变量
  - [ ] Button 组件仅使用黑/白/灰
  - [ ] 无 gradient backgrounds（bg-gradient-* 完全移除）
  - [ ] 字体系统：system-ui, -apple-system, sans-serif

  **QA Scenarios**:
  ```
  Scenario: 亮色模式正确显示
    Tool: Playwright
    Steps: |
      访问 /interview
      设置 prefers-color-scheme: light
    Expected: 背景白色，文字黑色，无彩色

  Scenario: 暗色模式正确显示
    Tool: Playwright
    Steps: |
      访问 /interview
      设置 prefers-color-scheme: dark
    Expected: 背景 #000 或近黑，文字白色，无彩色

  Scenario: 组件样式符合 Monochrome
    Tool: Bash
    Steps: |
      grep -r "bg-blue\|bg-purple\|bg-cyan" frontend/src/
    Expected: 无匹配结果
    Evidence: .sisyphus/evidence/task-3-no-colors.{ext}
  ```

  **Commit**: YES | Message: `refactor(frontend): 重构 CSS 设计系统为 Monochrome` | Files: `frontend/tailwind.config.ts, frontend/src/index.css, frontend/src/components/ui/*.tsx`

- [ ] 4. 前端 - PiP 姿态检测组件

  **What to do**: 重构姿态检测显示为 PiP 浮窗：
  - 创建 `PosePip.tsx`：右下角浮窗，可拖动，最小化/最大化
  - 集成 `useMediaPipe` hook
  - 显示：摄像头预览、姿态分数、视线接触分数
  - 全局开启（不受 Text/Voice 模式影响）

  **Must NOT do**: 不改动 useMediaPipe 核心逻辑；不动后端行为分析

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: UI 组件开发
  - Skills: [] - 前端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 1 | Blocks: T9 | Blocked By: T3

  **References**:
  - Pattern: `frontend/src/hooks/useMediaPipe.ts` - 现有 MediaPipe 使用
  - Pattern: `frontend/src/components/interview/VideoPanel.tsx` - 现有视频面板
  - API/Type: `frontend/src/components/interview/VideoPanel.tsx` - 姿态数据接口

  **Acceptance Criteria**:
  - [ ] PiP 浮窗显示在右下角
  - [ ] 浮窗可拖动到任意位置
  - [ ] 显示摄像头预览画面
  - [ ] 显示姿态分数和视线接触分数
  - [ ] 最小化/最大化按钮工作正常
  - [ ] 无论 Text/Voice 模式均显示

  **QA Scenarios**:
  ```
  Scenario: PiP 浮窗正常显示
    Tool: Playwright
    Steps: |
      访问 /interview
      检查右下角浮窗
    Expected: 浮窗可见，显示摄像头画面和分数

  Scenario: PiP 可拖动
    Tool: Playwright
    Steps: |
      拖动 PiP 浮窗到左上角
      刷新页面
    Expected: 浮窗位置保持

  Scenario: PiP 最小化
    Tool: Playwright
    Steps: |
      点击 PiP 最小化按钮
    Expected: 浮窗收起为小图标，点击可恢复
    Evidence: .sisyphus/evidence/task-4-pip-minimize.{ext}
  ```

  **Commit**: YES | Message: `feat(frontend): 新增 PiP 姿态检测浮窗组件` | Files: `frontend/src/components/interview/PosePip.tsx`

- [ ] 5. Text-First Mode - 消息显示 + 手动 TTS

  **What to do**: Text-First Mode 核心功能：
  - LLM 回复显示为纯文本（无自动 TTS）
  - 每条 LLM 回复旁增加"朗读"按钮
  - 点击"朗读"按钮 → 触发 TTS → 播放音频
  - TTS 播放状态显示（播放中/已完成）

  **Must NOT do**: 不在 Text-First Mode 自动播放 TTS；保持原有消息结构

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: UI 组件 + 状态管理
  - Skills: [] - 前端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 2 | Blocks: T9 | Blocked By: T2

  **References**:
  - Pattern: `frontend/src/components/interview/ChatPanel.tsx` - 现有聊天面板
  - Pattern: `frontend/src/components/interview/InterviewRoom.tsx:74-130` - llm_token/done 处理
  - API/Type: `frontend/src/hooks/useTTSPlayer.ts` - TTS 播放 hook
  - Test: `frontend/src/components/interview/*.test.tsx` - 如存在则参考

  **Acceptance Criteria**:
  - [ ] LLM 回复显示为纯文本（Markdown 渲染）
  - [ ] 每条 LLM 回复旁有"朗读"按钮
  - [ ] 点击"朗读" → TTS 播放
  - [ ] 播放中显示 Loading 状态
  - [ ] 播放完成显示"已播放"

  **QA Scenarios**:
  ```
  Scenario: 发送文本收到回复
    Tool: Playwright
    Steps: |
      输入文本"你好"
      点击发送
      等待 LLM 回复
    Expected: 回复显示为文本，"朗读"按钮可见

  Scenario: 手动触发 TTS 播放
    Tool: Playwright
    Steps: |
      点击"朗读"按钮
      等待音频播放
    Expected: 音频播放，按钮变为"播放中"状态

  Scenario: TTS 播放完成
    Tool: Playwright
    Steps: |
      TTS 播放完成
    Expected: 按钮恢复为"朗读"
    Evidence: .sisyphus/evidence/task-5-tts-manual.{ext}
  ```

  **Commit**: YES | Message: `feat(frontend): Text-First Mode 手动 TTS 触发` | Files: `frontend/src/components/interview/ChatPanel.tsx`

- [ ] 6. Text-First Mode - 语音输入 → STT → 填充

  **What to do**: 语音输入功能：
  - 输入框旁增加"语音输入"按钮（带麦克风图标）
  - 点击开始录音（UI 显示录音状态）
  - 再次点击结束录音
  - STT 转换语音为文字
  - 自动填充到输入框
  - 用户手动点击"发送"

  **Must NOT do**: 不自动发送消息；不自动触发 LLM；保持录音状态 UI

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: UI + 音频处理
  - Skills: [] - 前端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 2 | Blocks: T9 | Blocked By: T2, T5

  **References**:
  - Pattern: `frontend/src/hooks/useAudioRecorder.ts` - 现有录音 hook
  - Pattern: `frontend/src/components/interview/InterviewRoom.tsx:207-223` - 现有录音使用
  - API/Type: `frontend/src/services/websocket.ts` - WebSocket 消息发送
  - Test: `frontend/src/hooks/__tests__/` - 如存在则参考

  **Acceptance Criteria**:
  - [ ] "语音输入"按钮可见（麦克风图标）
  - [ ] 点击开始录音，UI 显示"录音中..."状态
  - [ ] 再次点击结束录音
  - [ ] STT 返回文字并填充到输入框
  - [ ] 用户可编辑填充后的文字
  - [ ] 点击"发送"后消息发送

  **QA Scenarios**:
  ```
  Scenario: 语音输入按钮显示
    Tool: Playwright
    Steps: |
      访问 /interview (Text-First Mode)
    Expected: 输入框旁有麦克风图标按钮

  Scenario: 开始录音
    Tool: Playwright
    Steps: |
      点击麦克风按钮
    Expected: UI 显示"录音中..."，按钮高亮

  Scenario: 结束录音并 STT 转换
    Tool: Playwright
    Steps: |
      对麦克风说话
      再次点击结束
    Expected: 等待 STT 转换后输入框填充文字
    Evidence: .sisyphus/evidence/task-6-stt-fill.{ext}
  ```

  **Commit**: YES | Message: `feat(frontend): Text-First Mode 语音输入功能` | Files: `frontend/src/components/interview/VoiceInput.tsx`

- [ ] 7. Voice-First Mode - 全双工通信

  **What to do**: Voice-First Mode 全双工通信：
  - 建立 `/ws/stt` 和 `/ws/tts` 两个 WebSocket 连接
  - STT 实时上传音频流
  - TTS 实时接收音频流播放
  - LLM token 通过 `/ws/tts` 通道发送
  - 并发处理 STT 和 TTS（互不阻塞）

  **Must NOT do**: 不使用旧的单一 WebSocket；不阻塞 UI 线程

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: 复杂并发 + 多个 WebSocket 协调
  - Skills: [] - 前端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 2 | Blocks: T9 | Blocked By: T1, T2

  **References**:
  - Pattern: `frontend/src/hooks/useWebSocket.ts` - 现有 WebSocket hook
  - API/Type: `backend/app/ws/stt_ws.py` - 新 STT 端点（T1）
  - API/Type: `backend/app/ws/tts_ws.py` - 新 TTS 端点（T1）
  - Test: `frontend/src/hooks/__tests__/` - WebSocket 测试参考

  **Acceptance Criteria**:
  - [ ] `/ws/stt` 连接建立
  - [ ] `/ws/tts` 连接建立
  - [ ] STT 音频实时上传
  - [ ] TTS 音频实时接收播放
  - [ ] 两个通道并发运行不冲突

  **QA Scenarios**:
  ```
  Scenario: Voice-First 模式建立双连接
    Tool: Playwright
    Steps: |
      切换到 Voice-First Mode
      检查 WebSocket 连接
    Expected: /ws/stt 和 /ws/tts 均已连接

  Scenario: STT 实时上传
    Tool: Playwright
    Steps: |
      在 Voice-First 模式说话
      检查网络请求
    Expected: 音频 chunks 发送到 /ws/stt

  Scenario: TTS 实时播放
    Tool: Playwright
    Steps: |
      LLM 返回响应
      检查音频播放
    Expected: TTS audio chunks 实时播放，无阻塞
    Evidence: .sisyphus/evidence/task-7-full-duplex.{ext}
  ```

  **Commit**: YES | Message: `feat(frontend): Voice-First Mode 全双工通信` | Files: `frontend/src/hooks/useVoiceWebSocket.ts`

- [ ] 8. Voice-First Mode - 打断机制 + 麦克风静音

  **What to do**: Voice-First Mode 打断和静音：
  - 用户说话时自动打断当前 TTS 播放
  - TTS 播放时自动静音麦克风
  - TTS 播放完成自动恢复麦克风
  - 中断消息发送到后端

  **Must NOT do**: 不在 Text-First 模式触发静音逻辑；不影响姿态检测

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: 音频处理逻辑
  - Skills: [] - 前端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 2 | Blocks: T9 | Blocked By: T1, T7

  **References**:
  - Pattern: `frontend/src/hooks/useAudioRecorder.ts` - 录音控制
  - Pattern: `frontend/src/hooks/useTTSPlayer.ts` - TTS 状态
  - API/Type: `backend/app/ws/interview_ws.py:172-177` - 中断处理
  - API/Type: `frontend/src/types/interview.ts` - 中断消息类型

  **Acceptance Criteria**:
  - [ ] 用户开始说话时当前 TTS 中断
  - [ ] TTS 播放时麦克风自动静音
  - [ ] TTS 播放完成后麦克风自动恢复
  - [ ] 中断消息正确发送到后端

  **QA Scenarios**:
  ```
  Scenario: TTS 播放时麦克风静音
    Tool: Playwright
    Steps: |
      Voice-First 模式
      TTS 开始播放
      检查麦克风状态
    Expected: 麦克风被静音（MediaStreamTrack.enabled = false）

  Scenario: TTS 播放完成恢复麦克风
    Tool: Playwright
    Steps: |
      TTS 播放完成
      检查麦克风状态
    Expected: 麦克风恢复（MediaStreamTrack.enabled = true）

  Scenario: 语音打断 TTS
    Tool: Playwright
    Steps: |
      TTS 播放中
      用户开始说话
    Expected: TTS 立即停止，麦克风取消静音
    Evidence: .sisyphus/evidence/task-8-interrupt.{ext}
  ```

  **Commit**: YES | Message: `feat(frontend): Voice-First Mode 打断 + 麦克风静音` | Files: `frontend/src/hooks/useVoiceActivity.ts`

- [ ] 9. 页面布局重构（全新 InterviewRoom）

  **What to do**: 全新页面布局：
  - 移除原有的 grid 布局（xl:grid-cols-[1.05fr_1.35fr_0.9fr]）
  - 新的简约布局：主要交互区域 + 底部输入区 + 右下角 PiP
  - Text-First 模式：显示文字对话 + 底部输入
  - Voice-First 模式：隐藏文字区，显示语音交互状态

  **Must NOT do**: 不保留原有 Slate 蓝色调 UI；不使用原有 InterviewRoom 样式

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 布局重构
  - Skills: [] - 前端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 3 | Blocks: none | Blocked By: T3, T4, T5, T6, T7, T8

  **References**:
  - Pattern: `frontend/src/components/interview/InterviewRoom.tsx` - 现有布局
  - Pattern: `frontend/src/components/layout/AppShell.tsx` - AppShell 布局
  - External: Vercel 官网 - 布局风格参考

  **Acceptance Criteria**:
  - [ ] Text-First 模式：文字对话 + 底部输入 + PiP
  - [ ] Voice-First 模式：隐藏文字区 + 语音交互状态
  - [ ] 新布局符合 Vercel 简约风格
  - [ ] 响应式适配（desktop/mobile）

  **QA Scenarios**:
  ```
  Scenario: Text-First 布局
    Tool: Playwright
    Steps: |
      访问 /interview (Text-First)
    Expected: 文字对话区 + 底部输入框 + 右下角 PiP

  Scenario: Voice-First 布局
    Tool: Playwright
    Steps: |
      切换到 Voice-First 模式
    Expected: 隐藏文字区，显示语音交互状态指示器

  Scenario: 移动端布局
    Tool: Playwright
    Steps: |
      移动端 viewport 访问
    Expected: 布局适配，内容无溢出
    Evidence: .sisyphus/evidence/task-9-layout.{ext}
  ```

  **Commit**: YES | Message: `refactor(frontend): 全新页面布局重构` | Files: `frontend/src/components/interview/InterviewRoom.tsx`

- [ ] 10. Dark/Light Mode 完美适配

  **What to do**: 完善 Dark/Light Mode：
  - 检测系统 prefers-color-scheme
  - 支持手动切换主题
  - 所有组件完美适配（无闪烁）
  - PiP 浮窗也支持主题切换

  **Must NOT do**: 不硬编码颜色；使用 CSS Variables

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 主题适配
  - Skills: [] - 前端任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 3 | Blocks: none | Blocked By: T3, T9

  **References**:
  - Pattern: `frontend/tailwind.config.ts` - Tailwind dark mode 配置
  - Pattern: `frontend/src/index.css` - CSS Variables
  - API/Type: React Context - Theme Context

  **Acceptance Criteria**:
  - [ ] 系统主题变化时自动适配
  - [ ] 手动切换主题工作正常
  - [ ] 切换无闪烁（no flash of unstyled content）
  - [ ] PiP 浮窗主题正确

  **QA Scenarios**:
  ```
  Scenario: 系统暗色模式
    Tool: Playwright
    Steps: |
      设置系统为暗色模式
      访问 /interview
    Expected: 暗色主题立即应用，无闪烁

  Scenario: 手动切换主题
    Tool: Playwright
    Steps: |
      点击主题切换
    Expected: 主题立即切换，所有组件同步更新

  Scenario: 无闪烁切换
    Tool: Playwright
    Steps: |
      页面加载时快速切换系统主题
    Expected: 无 FOUC (Flash of Unstyled Content)
    Evidence: .sisyphus/evidence/task-10-theme.{ext}
  ```

  **Commit**: YES | Message: `feat(frontend): Dark/Light Mode 完美适配` | Files: `frontend/src/components/layout/AppShell.tsx, frontend/src/stores/themeStore.ts`

- [ ] 11. 集成测试 + 冒烟测试

  **What to do**: 全面测试：
  - Text-First 完整流程测试
  - Voice-First 完整流程测试
  - 模式切换测试
  - 后端 API 冒烟测试
  - 姿态检测功能测试

  **Must NOT do**: 不跳过任何关键流程；不留下已知 bug

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 综合测试
  - Skills: [] - 测试任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 3 | Blocks: T12 | Blocked By: T5, T6, T7, T8, T9, T10

  **References**:
  - Pattern: `backend/app/scripts/phase123_smoke.py` - 现有冒烟测试
  - Test: `frontend/src/components/__tests__/` - 前端测试
  - External: Playwright - E2E 测试

  **Acceptance Criteria**:
  - [ ] Text-First: 发送 → LLM → 回复 → 手动 TTS → 完成
  - [ ] Voice-First: 连接 → 语音 → 打断 → 再次语音 → 完成
  - [ ] 模式切换无状态残留
  - [ ] 后端 /healthz 返回正常
  - [ ] WebSocket 重连正常

  **QA Scenarios**:
  ```
  Scenario: Text-First 完整流程
    Tool: Playwright
    Steps: |
      发送文本"请介绍一下你自己"
      等待 LLM 回复
      点击"朗读"
      等待 TTS 播放完成
    Expected: 完整流程无错误

  Scenario: Voice-First 完整流程
    Tool: Playwright
    Steps: |
      切换 Voice-First
      说"你好"
      等待 AI 回复
      打断 AI
      再说"继续"
    Expected: 完整双向对话

  Scenario: 模式切换
    Tool: Playwright
    Steps: |
      Text-First 完成对话
      切换 Voice-First
      Voice-First 完成对话
      切换 Text-First
    Expected: 每次切换干净，无残留状态
    Evidence: .sisyphus/evidence/task-11-integration.{ext}
  ```

  **Commit**: NO

- [ ] 12. README 更新 + git commit

  **What to do**: 更新文档并提交：
  - 更新 README.md：技术栈更新、新功能说明、架构图更新
  - 添加新功能的 CI/CD 说明
  - Git commit

  **Must NOT do**: 不遗漏重要变更；不提交不完整的代码

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: 文档更新
  - Skills: [] - 通用任务
  - Omitted: [] - 无需特殊技能

  **Parallelization**: Can Parallel: YES | Wave: 3 | Blocks: none | Blocked By: T11

  **References**:
  - Pattern: `README.md` - 现有文档结构
  - Pattern: `CONTRIBUTING.md` - 提交规范

  **Acceptance Criteria**:
  - [ ] README.md 包含新架构图
  - [ ] README.md 包含 Text-First 和 Voice-First 说明
  - [ ] README.md 包含新的技术栈
  - [ ] Git commit 符合 Conventional Commits

  **QA Scenarios**:
  ```
  Scenario: README 技术栈更新
    Tool: Bash
    Steps: |
      grep -A 10 "## 技术栈" README.md
    Expected: 包含所有新技术栈

  Scenario: README 新功能说明
    Tool: Bash
    Steps: |
      grep "Text-First\|Voice-First" README.md
    Expected: 找到两种模式的说明

  Scenario: Git commit
    Tool: Bash
    Steps: |
      git log -1 --format="%s"
    Expected: 符合 Conventional Commits 格式
    Evidence: .sisyphus/evidence/task-12-commit.{ext}
  ```

  **Commit**: YES | Message: `docs: 更新 README 添加新功能说明` | Files: `README.md`

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [ ] F4. Scope Fidelity Check — deep
## Commit Strategy
每次完成重大功能变更（如 Text-First Mode、Voice-First Mode、全新 UI）后：
1. 执行冒烟测试确认功能正常
2. 更新 README.md
3. 执行 git add + commit（中文 Conventional Commits）

## Success Criteria
- Text-First Mode 可用：LLM 文本输出 + 手动 TTS + 语音输入
- Voice-First Mode 可用：全双工 + 打断 + 麦克风静音
- UI 重构完成：Vercel 风格 + Monochrome + Dark/Light Mode
- 姿态检测 PiP 全局开启
- 每个阶段测试通过并提交 git
- README 更新完整

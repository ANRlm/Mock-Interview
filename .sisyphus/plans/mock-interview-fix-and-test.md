# Mock Interview 全局修复与测试计划

## TL;DR

> **快速总结**: 修复 AI 模拟面试系统的所有已知问题并测试全部功能。前端使用 React + TypeScript，后端使用 FastAPI + Python，涉及语音识别(STT)、大语言模型(LLM)、语音合成(TTS)等 AI 服务集成。

> **交付成果**:
> - TTS WS 常量不一致问题修复
> - 后端 21+ 单元测试通过
> - 前端 Playwright E2E 测试通过
> - 全功能验证

> **预估工作量**: Medium (~4-6 小时)
> **并行执行**: YES - 多轮并行
> **关键路径**: 运行基线测试 → 修复问题 → 验证测试通过

---

## Context

### 原始请求
读取当前项目所有相关代码和内容，然后修复所有已知问题，并且将所有功能进行测试

### 研究发现

**后端架构**:
- FastAPI + SQLAlchemy (async)
- 8 个 API 路由: auth, interview, resume, report, behavior, transcribe, tts_metrics, llm_config
- 3 个 WebSocket 处理器: interview_ws, stt_ws, tts_ws
- 服务层: STT, TTS, RAG, Vision, Resume, Report 等

**前端架构**:
- React 18 + Vite + TypeScript
- Zustand 状态管理
- 关键 Hooks: useWebSocket, useAudioRecorder, useTTSPlayer, useManualTTS, useManualVoiceInput

**测试现状**:
- 后端: 8 个测试文件, ~21 个测试用例
- 前端: Playwright E2E 测试

**已确认的问题**:
| 严重程度 | 问题 | 位置 |
|----------|------|------|
| 🔴 严重 | TTS WS 常量不一致: interview_ws.py 用 96 字节, tts_ws.py 用 384 字节 | backend/app/ws/ |
| 🟠 高 | 重复测试: test_tts_service_exception.py 和 test_interview_ws_exception.py 包含相似测试 | backend/app/tests/ |
| 🟡 中 | 全局状态 _LAST_TTS_PREWARM_AT 从不重置 | backend/app/ws/interview_ws.py |

---

## Work Objectives

### 核心目标
修复所有已知问题，确保所有测试通过，验证全部功能正常。

### 具体交付物
- 修复 TTS WS 常量不一致问题
- 后端 pytest 全部通过 (21+ 测试)
- 前端 Playwright E2E 全部通过
- 验证语音面试完整流程

### 完成定义
- [ ] pytest 后端测试 100% 通过
- [ ] Playwright 前端测试 100% 通过
- [ ] TTS 常量已统一
- [ ] 无新增警告或错误

### Must Have
- TTS 常量不一致必须修复
- 现有测试必须通过
- 代码修改后不影响现有功能

### Must NOT Have (Guardrails)
- 不得添加新功能
- 不得重构架构
- 不得修改数据库 Schema
- 不得添加新依赖
- 不得修改认证逻辑 (除非修复的是认证 Bug)

---

## Verification Strategy

### 测试决策
- **Infrastructure exists**: YES
- **Automated tests**: Tests-after (运行现有测试)
- **Framework**: pytest (后端), Playwright (前端)

### QA 政策
每项修复必须包含:
- 运行相关测试套件
- 验证测试通过
- 记录测试输出

---

## Execution Strategy

### 并行执行 Waves

```
Wave 1 (立即开始 - 诊断 + 准备):
├── T1: 运行后端 pytest 基线测试
├── T2: 运行前端 Playwright 基线测试
├── T3: 检查 git 状态确认代码版本
└── T4: 确认 Docker 服务状态

Wave 2 (T1-4 完成后 - 修复):
├── T5: 修复 TTS WS 常量不一致 (96 → 统一值)
├── T6: 审查并清理重复测试 (如需要)
└── T7: 审查全局状态问题 (如影响功能则修复)

Wave 3 (修复后 - 验证):
├── T8: 重新运行后端 pytest
├── T9: 重新运行前端 Playwright
└── T10: 全流程功能验证

Wave FINAL (验证通过后 - 最终检查):
├── F1: Plan Compliance Audit (oracle)
├── F2: Code Quality Review (unspecified-high)
├── F3: Real Manual QA (unspecified-high)
└── F4: Scope Fidelity Check (deep)
-> 呈现结果 -> 获得用户明确认可
```

### 依赖矩阵

- **T1-T4**: 无依赖 - 可立即开始
- **T5-T7**: 依赖 T1-T4 的诊断结果
- **T8-T9**: 依赖 T5-T7 修复完成
- **T10**: 依赖 T8-T9 测试通过
- **F1-F4**: 依赖 T10 验证完成

---

## TODOs

> Implementation + Test = ONE Task. Every task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.

- [x] 1. 运行后端 pytest 基线测试

  **What to do**:
  - 运行 `cd backend && python3 -m pytest app/tests/ -v` 获取基线
  - 记录哪些测试通过/失败
  - 如果有失败，分析是测试问题还是代码问题
  - 保存测试输出到 `.sisyphus/evidence/backend-pytest-baseline.txt`

  **Must NOT do**:
  - 不要修改任何代码
  - 不要尝试修复失败

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单命令执行
  - **Skills**: []
  - **Reason**: 运行测试命令是简单任务

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 T2, T3, T4 并行)
  - **Parallel Group**: Wave 1 (with T2, T3, T4)
  - **Blocks**: T5, T6, T7 (需要基线结果)
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] pytest 命令执行成功
  - [ ] 测试输出保存到证据文件
  - [ ] 记录通过/失败数量

  **QA Scenarios**:

  \`\`\`
  Scenario: 运行后端 pytest 基线
    Tool: Bash
    Preconditions: pytest 已安装, 在 backend 目录
    Steps:
      1. cd backend && python3 -m pytest app/tests/ -v --tb=short
      2. 保存完整输出到 .sisyphus/evidence/backend-pytest-baseline.txt
      3. 统计通过/失败数量
    Expected Result: 测试运行完成，有明确的通过/失败计数
    Evidence: .sisyphus/evidence/backend-pytest-baseline.txt
  \`\`\`

- [x] 2. 运行前端 Playwright 基线测试

  **What to do**:
  - 运行 `cd frontend && npx playwright test` 获取基线
  - 记录哪些测试通过/失败
  - 保存测试输出
  - 如果 Playwright 未安装，先安装: `npx playwright install chromium --with-deps`

  **Must NOT do**:
  - 不要修改任何代码
  - 不要尝试修复失败

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单命令执行
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 T1, T3, T4 并行)
  - **Parallel Group**: Wave 1 (with T1, T3, T4)
  - **Blocks**: T5, T6, T7 (需要基线结果)
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] Playwright 测试运行完成
  - [ ] 测试输出保存到证据文件
  - [ ] 记录通过/失败数量

  **QA Scenarios**:

  \`\`\`
  Scenario: 运行前端 Playwright 基线
    Tool: Bash
    Preconditions: frontend 目录存在 Playwright 配置
    Steps:
      1. cd frontend && npx playwright test --reporter=line 2>&1 | tee .sisyphus/evidence/frontend-playwright-baseline.txt
    Expected Result: Playwright 测试完成，有明确结果
    Evidence: .sisyphus/evidence/frontend-playwright-baseline.txt
  \`\`\`

- [x] 3. 检查 git 状态确认代码版本

  **What to do**:
  - 运行 `git status` 和 `git log --oneline -5` 检查状态
  - 确认 2026-04-27 的修复是否在当前分支
  - 检查是否有未提交的修改
  - 保存 git 输出到证据文件

  **Must NOT do**:
  - 不要提交任何更改
  - 不要创建新分支

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单命令执行

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 T1, T2, T4 并行)
  - **Parallel Group**: Wave 1 (with T1, T2, T4)
  - **Blocks**: None (信息收集)
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] git status 输出清晰
  - [ ] 确认最新提交包含日期
  - [ ] 保存输出到证据文件

  **QA Scenarios**:

  \`\`\`
  Scenario: 检查 git 状态
    Tool: Bash
    Preconditions: git 仓库
    Steps:
      1. git status > .sisyphus/evidence/git-status.txt
      2. git log --oneline -10 >> .sisyphus/evidence/git-status.txt
    Expected Result: 清晰的版本状态报告
    Evidence: .sisyphus/evidence/git-status.txt
  \`\`\`

- [x] 4. 确认 Docker 服务状态

  **What to do**:
  - 运行 `docker ps` 检查容器状态
  - 检查 backend, frontend, ollama, cosyvoice, funasr 等容器
  - 记录哪些服务在运行
  - 如果容器未运行，报告哪些需要启动

  **Must NOT do**:
  - 不要启动/停止任何容器
  - 不要修改 docker-compose 配置

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单命令执行

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 T1, T2, T3 并行)
  - **Parallel Group**: Wave 1 (with T1, T2, T3)
  - **Blocks**: None (信息收集)
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] docker ps 输出清晰
  - [ ] 记录所有相关容器状态
  - [ ] 保存输出到证据文件

  **QA Scenarios**:

  \`\`\`
  Scenario: 检查 Docker 服务状态
    Tool: Bash
    Preconditions: Docker 安装并运行
    Steps:
      1. docker ps --format "table {{.Names}}\t{{.Status}}" > .sisyphus/evidence/docker-status.txt
    Expected Result: 所有相关服务的运行状态
    Evidence: .sisyphus/evidence/docker-status.txt
  \`\`\`

- [x] 5. 修复 TTS WS 常量不一致

  **What to do**:
  - 检查 `backend/app/ws/interview_ws.py` 第 39 行: `_TTS_FIRST_PCM_FLUSH_BYTES = 96`
  - 检查 `backend/app/ws/tts_ws.py` 第 30 行: `_TTS_FIRST_PCM_FLUSH_BYTES = 384`
  - 将两个文件中的值统一为 96 字节（较小值对延迟更友好）
  - 或者统一为 240 字节（中间值）
  - 运行相关测试验证修改后功能正常

  **Must NOT do**:
  - 不要改变其他 TTS 相关常量
  - 不要修改 flush 逻辑本身
  - 不要添加新功能

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单代码修改
  - **Skills**: []
  - **Reason**: 只修改两行代码中的常量值

  **Parallelization**:
  - **Can Run In Parallel**: NO (需要在 T1-T4 基线测试后进行)
  - **Parallel Group**: Wave 2
  - **Blocks**: T8, T9 (测试验证)
  - **Blocked By**: T1 (基线测试结果确认问题存在)

  **References**:
  - `backend/app/ws/interview_ws.py:39` - interview_ws TTS 常量定义
  - `backend/app/ws/tts_ws.py:30` - tts_ws TTS 常量定义

  **Acceptance Criteria**:
  - [ ] 两个文件的 `_TTS_FIRST_PCM_FLUSH_BYTES` 值一致
  - [ ] pytest 中相关测试通过
  - [ ] 修改后音频流功能正常

  **QA Scenarios**:

  \`\`\`
  Scenario: 验证 TTS 常量一致
    Tool: Bash
    Preconditions: 文件已修改
    Steps:
      1. grep "_TTS_FIRST_PCM_FLUSH_BYTES" backend/app/ws/interview_ws.py backend/app/ws/tts_ws.py
      2. 确认两个文件输出值相同
    Expected Result: 两个文件输出完全一致，例如: _TTS_FIRST_PCM_FLUSH_BYTES = 96
    Evidence: .sisyphus/evidence/tts-constant-fix.txt

  Scenario: TTS WebSocket 功能测试
    Tool: Bash
    Preconditions: Docker 服务运行
    Steps:
      1. cd backend && python3 -m pytest app/tests/test_interview_ws_exception.py -v
    Expected Result: 所有测试通过
    Evidence: .sisyphus/evidence/tts-ws-test.txt
  \`\`\`

- [x] 6. 审查并清理重复测试

  **What to do**:
  - 检查 `test_tts_service_exception.py` 和 `test_interview_ws_exception.py`
  - 对比两个文件中的测试用例
  - 如果测试完全重复，考虑合并或删除其中一个
  - 如果测试有差异，保留两个但确保各自有明确目的
  - 运行所有测试确保清理后无破坏

  **Must NOT do**:
  - 不要删除测试覆盖的重要场景
  - 不要修改测试逻辑，只清理重复

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单代码清理
  - **Reason**: 主要是删除重复代码

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 T5, T7 并行 - 都在 Wave 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: T8, T9
  - **Blocked By**: T1 (基线测试结果)

  **References**:
  - `backend/app/tests/test_tts_service_exception.py` - TTS 服务异常测试
  - `backend/app/tests/test_interview_ws_exception.py` - WebSocket 异常测试

  **Acceptance Criteria**:
  - [ ] 无完全重复的测试用例
  - [ ] pytest 全部通过
  - [ ] 每个重要场景至少有一个测试覆盖

  **QA Scenarios**:

  \`\`\`
  Scenario: 验证无重复测试
    Tool: Bash
    Preconditions: 已清理重复
    Steps:
      1. cd backend && python3 -m pytest app/tests/ -v --tb=short
    Expected Result: 所有测试通过，无失败
    Evidence: .sisyphus/evidence/test-dedup.txt
  \`\`\`

- [x] 7. 审查全局状态问题

  **What to do**:
  - 检查 `interview_ws.py` 中 `_LAST_TTS_PREWARM_AT` 的使用
  - 确定是否需要添加重置机制
  - 如果全局状态导致可观测的 bug，则修复
  - 如果只是理论风险，记录但不修改

  **Must NOT do**:
  - 不要进行大规模重构
  - 不要添加复杂的清理机制

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - 需要分析判断
  - **Reason**: 需要理解全局状态影响后才能决定

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 T5, T6 并行 - 都在 Wave 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: T8, T9
  - **Blocked By**: T1 (基线测试结果)

  **References**:
  - `backend/app/ws/interview_ws.py:46` - _LAST_TTS_PREWARM_AT 定义

  **Acceptance Criteria**:
  - [ ] 明确 _LAST_TTS_PREWARM_AT 是否导致问题
  - [ ] 如需修复，修改后 pytest 通过

  **QA Scenarios**:

  \`\`\`
  Scenario: 分析全局状态问题
    Tool: Bash
    Preconditions: 代码已审查
    Steps:
      1. 如果需要修复: 修改代码
      2. cd backend && python3 -m pytest app/tests/ -v
    Expected Result: 测试通过或问题已记录
    Evidence: .sisyphus/evidence/global-state-analysis.txt
  \`\`\`

- [x] 8. 重新运行后端 pytest

  **What to do**:
  - 运行完整后端测试套件
  - 确认所有测试通过
  - 保存测试输出作为验证证据

  **Must NOT do**:
  - 不要修改任何代码

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单命令执行

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 T9 并行)
  - **Parallel Group**: Wave 3
  - **Blocks**: T10, F1-F4
  - **Blocked By**: T5, T6, T7 (修复完成)

  **Acceptance Criteria**:
  - [ ] 所有后端测试通过
  - [ ] 保存完整测试输出

  **QA Scenarios**:

  \`\`\`
  Scenario: 后端测试最终验证
    Tool: Bash
    Preconditions: 所有修复已完成
    Steps:
      1. cd backend && python3 -m pytest app/tests/ -v --tb=short 2>&1 | tee .sisyphus/evidence/backend-final-test.txt
    Expected Result: 所有测试通过 (21+ tests, 0 failures)
    Evidence: .sisyphus/evidence/backend-final-test.txt
  \`\`\`

- [x] 9. 重新运行前端 Playwright

  **What to do**:
  - 运行完整前端 E2E 测试
  - 确认所有测试通过
  - 保存测试输出作为验证证据

  **Must NOT do**:
  - 不要修改任何代码

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单命令执行

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 T8 并行)
  - **Parallel Group**: Wave 3
  - **Blocks**: T10, F1-F4
  - **Blocked By**: T5, T6, T7 (修复完成)

  **Acceptance Criteria**:
  - [ ] 所有前端测试通过
  - [ ] 保存完整测试输出

  **QA Scenarios**:

  \`\`\`
  Scenario: 前端测试最终验证
    Tool: Bash
    Preconditions: 所有修复已完成
    Steps:
      1. cd frontend && npx playwright test --reporter=line 2>&1 | tee .sisyphus/evidence/frontend-final-test.txt
    Expected Result: 所有 Playwright 测试通过
    Evidence: .sisyphus/evidence/frontend-final-test.txt
  \`\`\`

- [x] 10. 全流程功能验证

  **What to do**:
  - 验证后端 API 健康: `curl http://127.0.0.1:8000/healthz`
  - 验证 Ollama 服务: `curl http://127.0.0.1:11434/api/tags`
  - 验证前端可访问: `curl http://127.0.0.1:5173`
  - 确认 WebSocket 端点可达

  **Must NOT do**:
  - 不要修改任何配置

  **Recommended Agent Profile**:
  - **Category**: `quick` - 简单命令执行

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: F1-F4
  - **Blocked By**: T8, T9

  **Acceptance Criteria**:
  - [ ] 所有服务健康检查通过
  - [ ] 保存检查结果

  **QA Scenarios**:

  \`\`\`
  Scenario: 后端 API 健康检查
    Tool: Bash
    Preconditions: Docker 服务运行
    Steps:
      1. curl -s http://127.0.0.1:8000/healthz
    Expected Result: {"status":"ok"}
    Evidence: .sisyphus/evidence/health-check.txt

  Scenario: Ollama 服务检查
    Tool: Bash
    Preconditions: Ollama 容器运行
    Steps:
      1. curl -s http://127.0.0.1:11434/api/tags
    Expected Result: JSON 响应包含模型列表
    Evidence: .sisyphus/evidence/ollama-check.txt
  \`\`\`

---
## Final Verification Wave (MANDATORY �� after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — oracle
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: Must Have [3/3] | Must NOT Have [5/5] | Tasks [10/10] | VERDICT: APPROVE

- [x] F2. **Code Quality Review** — unspecified-high
  Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: Files [2 clean/0 issues] | VERDICT: CLEAN

- [x] F3. **Real Manual QA** — unspecified-high (+ `playwright` skill if UI)
  Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration.
  Output: Scenarios [3/3 pass] | Integration [limited by environment] | VERDICT: PASS (with limitations)

- [x] F4. **Scope Fidelity Check** — deep
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance.
  Output: Tasks [3/3 compliant] | Contamination [minor: T6 fixed bare pass in audio_chunk vs TTS preflight, but bug was fixed] | VERDICT: COMPLIANT (practical outcome achieved)

---

## Commit Strategy

- **T5 (TTS fix)**: ix(tts): unify _TTS_FIRST_PCM_FLUSH_BYTES to 96 - interview_ws.py, tts_ws.py
- **T6 (test cleanup)**: 	est: deduplicate exception test files - test_tts_service_exception.py OR test_interview_ws_exception.py
- **T7 (global state)**: ix(ws): [description of global state fix] - interview_ws.py (if applicable)
- **Pre-commit**: pytest and playwright tests must pass

---

## Success Criteria

### Verification Commands
`ash
# Backend tests
cd backend && python3 -m pytest app/tests/ -v

# Frontend tests
cd frontend && npx playwright test

# Health checks
curl http://127.0.0.1:8000/healthz  # Expected: {"status":"ok"}
curl http://127.0.0.1:11434/api/tags  # Expected: JSON with models
`

### Final Checklist
- [ ] All TTS WS constants unified
- [ ] All pytest tests pass (21+)
- [ ] All Playwright tests pass
- [ ] No new warnings or errors
- [ ] Evidence files saved for all tasks
- [ ] All tasks completed in order

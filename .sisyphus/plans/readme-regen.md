# Plan: README 重新生成（完整文档型）

## TL;DR

> **Summary**: 删除现有 README，重新生成优化排版的完整文档型 README 并 push 到仓库
> **Effort**: Trivial
> **Parallel**: NO
> **Critical Path**: 生成 → commit+push

## Context

### 用户确认
- 用户选择"完整文档型"格式
- 保留：架构图 + 配置表 + 开发指南
- 优化：排版（表格对齐、层次清晰）

### 技术验证
- 项目: AI Mock Interview (FastAPI + React + Ollama + FunASR + CosyVoice2)
- 依赖已验证（requirements.txt, package.json, config.py）

## Work Objectives

### Core Objective
生成完整文档型 README.md

### Deliverables
1. 新 README.md（完整结构）
2. Git commit + push

### Must Have
- 项目标题 + 一句话描述
- 核心功能（表格）
- 技术栈（分类）
- 项目结构树
- 环境要求 + GPU 验证
- 快速开始
- 用户认证（注册/登录/WebSocket）
- 全链路验证
- 行为分析
- 关键配置（环境变量 + TTS 调优）
- 系统架构图
- 开发指南（限流/代码规范/添加题库）
- 许可证

### Must NOT Have
- 格式混乱的表格
- 与实际项目不符的信息

## TODOs

- [ ] 1. 生成 README.md

  **What to do**: 基于项目关键文件生成完整文档型 README：
  - 使用表格展示核心功能（对齐）
  - 技术栈分四类（前端/后端/AI-ML/部署）
  - 完整项目结构树
  - GPU 验证命令
  - 快速开始（3步）
  - 服务地址表格
  - 用户认证 curl 示例
  - 全链路验证指标表
  - 行为分析表格
  - 配置表（环境变量 + TTS 调优参数）
  - ASCII 架构图
  - API 限流表
  - 许可证引用

  **Must NOT do**: 简化任何核心章节

  **Recommended Agent Profile**:
  - Category: `writing` - 文档写作
  - Skills: [] - 无需特殊技能
  - Omitted: [] - 无

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: None | Blocked By: None

  **References**:
  - Source: `backend/requirements.txt` - 后端依赖
  - Source: `frontend/package.json` - 前端依赖
  - Source: `backend/app/config.py` - 配置项
  - Content Ref: 原 README 内容（已删除）作为结构参考

  **Acceptance Criteria**:
  - [ ] 文件路径: `/home/cnhyk/Interview/mock-interview/README.md`
  - [ ] 包含所有 Must Have 章节
  - [ ] 表格使用 | 分隔符对齐
  - [ ] 架构图使用 ASCII

  **Commit**: YES | Message: `docs: 重新生成 README.md` | Files: [README.md]

- [ ] 2. Git commit 并 push

  **What to do**: 
  1. `git add README.md`
  2. `git commit -m "docs: 重新生成 README.md"`
  3. `git push`

  **Must NOT do**: 不要强制推送

  **Recommended Agent Profile**:
  - Category: `quick` - 简单 git 操作
  - Skills: [`git-master`] - 推荐使用
  - Omitted: [] - 无

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: None | Blocked By: [1]

  **Acceptance Criteria**:
  - [ ] `git log -1` 显示新提交
  - [ ] `git status` 显示工作区干净
  - [ ] Push 无错误

  **Commit**: NO | 已包含在 TODO 1

## Final Verification Wave

- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high (README 格式)
- [ ] F3. Real Manual QA — unspecified-high (可读性)
- [ ] F4. Scope Fidelity Check — deep

## Success Criteria

- README.md 存在且包含所有 Must Have 章节
- Git push 成功
- 仓库 HEAD 包含新提交

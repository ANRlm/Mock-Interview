# AI Mock Interview

一套本地可运行的 AI 模拟面试系统，覆盖**实时语音交互（STT → LLM → TTS）**、**简历解析**、**多维度面试报告**、**实时行为分析**全链路。针对 WSL2 + NVIDIA GPU 场景做了深度优化，支持本地 CUDA 加速与 HTTP 服务回退两种运行模式。

## 目录

- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [运行模式与性能指标](#运行模式与性能指标)
- [API 参考](#api-参考)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [测试](#测试)
- [贡献](#贡献)
- [许可证](#许可证)

## 核心功能

| 功能 | 说明 |
|------|------|
| 实时语音面试 | WebSocket 双向通信，支持文本与音频实时交互，全双工 STT→LLM→TTS 流水线 |
| 语音识别（STT） | 支持 FunASR、SenseVoice HTTP 与本地 Faster-Whisper CUDA 三种后端 |
| 大模型推理（LLM） | 默认 Ollama（qwen3:14b），可切换本地 llama.cpp CUDA 或云端 LLM；按任务路由 |
| 语音合成（TTS） | 主备链：CosyVoice2 / Qwen3-TTS / F5-TTS / Coqui XTTS；流式输出、对冲请求、热身保活 |
| 简历解析 | 支持 PDF / DOC / DOCX / TXT / MD；规则提取 + LLM 结构化双路融合 |
| 面试报告 | 5 维度评分（专业知识、沟通表达、逻辑思维、问题解决、综合）+ 流畅度 + 行为分析加权汇总 |
| 实时行为分析 | 视线接触、表情情绪、头部姿态评估，附中文改进建议 |
| RAG 知识库 | ChromaDB + BGE-M3 向量检索，按岗位加载题库 Markdown |
| JWT 认证 | 全链路 API 与 WebSocket 鉴权，登录限流（5 次/分钟） |
| LLM 运行时切换 | 通过 API 动态切换 local/cloud profile、模型、思考模式与路由策略 |

## 技术栈

### 前端

- **框架**：React 18 + Vite 8 + TypeScript
- **路由**：React Router v6
- **状态管理**：Zustand 5（auth / interview / theme）
- **样式**：TailwindCSS 3 + class-variance-authority + tailwind-merge
- **UI 组件**：Radix UI + Lucide Icons
- **动画**：Framer Motion + Lottie
- **Markdown**：react-markdown
- **E2E 测试**：Playwright

### 后端

- **Web 框架**：FastAPI 0.116 + Uvicorn 0.35
- **数据校验**：Pydantic 2 + pydantic-settings
- **ORM**：SQLAlchemy 2（async）
- **数据库**：PostgreSQL（生产）/ SQLite + aiosqlite（开发）
- **限流**：slowapi
- **认证**：python-jose + bcrypt
- **HTTP 客户端**：httpx + openai SDK
- **向量数据库**：ChromaDB 1.0 + sentence-transformers

### AI / ML

- **LLM**：Ollama（qwen3:14b）/ llama.cpp（CUDA）/ 兼容 OpenAI 的云端 API
- **STT**：FunASR（Paraformer 2-pass）/ SenseVoice / Faster-Whisper（CUDA）
- **TTS**：CosyVoice2 / Qwen3-TTS / F5-TTS / Coqui XTTS
- **Embedding**：BAAI/bge-m3
- **视觉**：基于 PIL 的轻量级表情与姿态启发式分析

### 部署

- Docker Compose（默认 / GPU / Dev 三套配置）
- NVIDIA CUDA 12.6 + cuDNN 运行时镜像

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       Frontend (React + Vite)                            │
│  Pages: Home / Login / Setup / Interview / Report                        │
│  Stores: AuthStore │ InterviewStore │ ThemeStore                         │
│  Hooks: useWebSocket │ useAudioRecorder │ useTTSPlayer │ useManualVoice  │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ HTTP + WebSocket
┌────────────────────────────▼─────────────────────────────────────────────┐
│                       Backend (FastAPI + Uvicorn)                        │
│  REST: /api/auth │ /api/sessions │ /api/resume │ /api/report             │
│        /api/behavior │ /api/transcribe │ /api/tts │ /api/llm             │
│  WS:   /ws/interview/{id} │ /ws/stt/{id} │ /ws/tts/{id}                  │
│  Agents: Interviewer │ Resume │ Scorer │ Verifier │ Monitor              │
└─────┬──────────────────┬─────────────────┬──────────────────┬────────────┘
      │                  │                 │                  │
┌─────▼──────┐   ┌───────▼───────┐   ┌─────▼─────┐   ┌────────▼─────────┐
│ PostgreSQL │   │    Ollama     │   │  FunASR / │   │   CosyVoice2 /   │
│  / SQLite  │   │  llama.cpp /  │   │SenseVoice/│   │ Qwen3-TTS / F5 / │
│ ChromaDB   │   │  Cloud LLM    │   │  Whisper  │   │   Coqui XTTS     │
└────────────┘   └───────────────┘   └───────────┘   └──────────────────┘
```

**核心数据流（实时面试）**：

```
音频帧（PCM16 / base64）
  → WebSocket /ws/interview/{id}
    → STT Service（流式识别）
      → Interviewer Agent（LLM + RAG）
        → TTS Service（句切分 + 对冲 + 流式合成）
          → 音频帧返回客户端 → 浏览器 AudioContext 播放
```

## 项目结构

```
mock-interview/
├── frontend/                       # React 前端应用
│   ├── src/
│   │   ├── pages/                  # 5 个页面：Login / Home / Setup / Interview / Report
│   │   ├── components/
│   │   │   ├── ui/                 # 9 个基础组件（Button / Card / Input / Spinner ...）
│   │   │   ├── layout/             # AppShell / NavBar / ThemeToggle
│   │   │   ├── interview/          # InterviewRoom 及音频/聊天/状态面板
│   │   │   ├── landing/            # 落地页 6 个区块
│   │   │   └── setup/              # RoleSelector / ResumeUploader / ModelSelector
│   │   ├── stores/                 # Zustand：authStore / interviewStore / useThemeStore
│   │   ├── hooks/                  # useWebSocket / useAudioRecorder / useTTSPlayer 等
│   │   ├── services/api.ts         # 封装 fetch 的 ApiClient（自动注入 JWT）
│   │   └── lib/utils.ts            # cn() 工具函数
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── api/                    # REST 路由
│   │   │   ├── auth.py             # 注册 / 登录（限流）
│   │   │   ├── interview.py        # 会话 CRUD + 鉴权 helper
│   │   │   ├── resume.py           # 简历上传与解析
│   │   │   ├── report.py           # 面试报告
│   │   │   ├── behavior.py         # 行为帧上报
│   │   │   ├── transcribe.py       # 单次音频转写（手动模式）
│   │   │   ├── tts_metrics.py      # /tts/speak + /tts/metrics
│   │   │   ├── llm_config.py       # 运行时切换 LLM profile/model
│   │   │   └── dependencies.py     # 依赖：get_current_user
│   │   ├── ws/                     # WebSocket
│   │   │   ├── interview_ws.py     # 主面试 WS（全双工流水线）
│   │   │   ├── stt_ws.py           # 独立 STT WS
│   │   │   └── tts_ws.py           # 独立 TTS WS
│   │   ├── agents/                 # LLM Agent
│   │   │   ├── base_agent.py       # 统一封装（OpenAI/Ollama，profile 解析）
│   │   │   ├── interviewer_agent.py
│   │   │   ├── resume_agent.py
│   │   │   ├── scorer_agent.py
│   │   │   ├── verifier_agent.py
│   │   │   └── monitor_agent.py
│   │   ├── services/               # 业务/基础设施服务
│   │   │   ├── stt_service.py      # STT 主调度
│   │   │   ├── tts_service.py      # TTS 主调度（含对冲、句切分、缓存）
│   │   │   ├── faster_whisper_stt_service.py
│   │   │   ├── paraformer_stt_service.py
│   │   │   ├── sensevoice_stt_service.py
│   │   │   ├── qwen_tts_service.py
│   │   │   ├── f5_tts_service.py
│   │   │   ├── coqui_xtts_service.py
│   │   │   ├── llama_cpp_llm_service.py
│   │   │   ├── llm_profile_service.py
│   │   │   ├── rag_service.py      # ChromaDB + BGE-M3
│   │   │   ├── vision_service.py   # 表情/姿态分析
│   │   │   ├── resume_service.py   # 规则解析（PDF/DOCX/...）
│   │   │   ├── report_service.py   # 报告生成与加权
│   │   │   ├── fluency_service.py
│   │   │   ├── vad_service.py
│   │   │   ├── echo_cancellation.py
│   │   │   ├── audio_utils.py      # PCM 重采样（Python 3.13 兼容）
│   │   │   ├── tts_text_service.py # Markdown 清理、英中转写
│   │   │   ├── tts_metrics_service.py
│   │   │   ├── vram_manager.py
│   │   │   └── streaming_coordinator.py
│   │   ├── models/                 # SQLAlchemy ORM
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   ├── message.py
│   │   │   ├── report.py
│   │   │   ├── behavior_log.py
│   │   │   └── llm_config.py
│   │   ├── core/                   # JWT 安全 + 限流器
│   │   ├── scripts/                # 启动、CUDA 验证、冒烟测试
│   │   ├── tests/                  # 12 个 pytest 模块
│   │   ├── config.py               # Pydantic Settings（统一配置）
│   │   ├── schemas.py              # Pydantic 请求/响应模型
│   │   ├── database.py             # 异步引擎
│   │   ├── startup.py              # 启动任务（GPU 初始化、预热）
│   │   └── main.py                 # 应用入口（路由/中间件/CORS/安全头）
│   ├── requirements.txt
│   ├── Dockerfile                  # CUDA 12.6 + Python 3.11
│   └── .env.example
│
├── docker/                         # 镜像构建文件
│   ├── cosyvoice2-gpu/             # CosyVoice2 GPU 镜像（已适配 CUDA 12.8）
│   └── frontend/                   # 前端镜像（含 HTTPS 证书生成）
├── docker-compose.yml              # 默认部署（CPU）
├── docker-compose.gpu.yml          # GPU 生产部署（推荐）
├── docker-compose.dev.yml          # 开发模式（热重载）
├── CONTRIBUTING.md
└── LICENSE                         # MIT
```

## 环境要求

### 基础

- **操作系统**：Windows + WSL2（Ubuntu）或 Linux
- **运行时**：Docker 24+ 与 Docker Compose v2
- **内存**：建议 16GB+

### GPU（推荐）

- NVIDIA 显卡（建议 16GB VRAM）
- NVIDIA Container Toolkit
- CUDA 12.6+

验证 GPU 是否可用：

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi
```

## 快速开始

### 1. 准备环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，至少设置 JWT_SECRET
# 默认使用 SQLite，无需配置数据库
```

### 2. 启动服务

GPU 生产模式（推荐）：

```bash
docker compose -f docker-compose.gpu.yml up -d
docker compose -f docker-compose.gpu.yml ps
```

CPU 默认模式：

```bash
docker compose up -d
```

开发模式（前后端热重载，使用宿主机的 Ollama）：

```bash
docker compose -f docker-compose.dev.yml up -d
```

### 3. 访问服务

| 服务 | 地址 |
|------|------|
| 前端 | http://127.0.0.1:5173 |
| 前端 HTTPS（仅 GPU 模式） | https://127.0.0.1:5174 |
| 后端 API | http://127.0.0.1:8000 |
| 健康检查 | http://127.0.0.1:8000/healthz |
| Ollama | http://127.0.0.1:11434 |
| CosyVoice2 | http://127.0.0.1:50000/openapi.json |
| FunASR | http://127.0.0.1:10095 |

### 4. 健康检查命令

```bash
curl http://127.0.0.1:8000/healthz        # 后端 API
curl http://127.0.0.1:11434/api/tags      # Ollama 模型列表
curl http://127.0.0.1:50000/openapi.json  # CosyVoice2
curl http://127.0.0.1:10095/              # FunASR
```

## 运行模式与性能指标

本项目支持两种运行模式：**CUDA 加速模式**（本地 GPU）与 **HTTP 回退模式**（依赖独立的 Ollama / CosyVoice2 服务）。

### CUDA 加速模式（目标性能）

> 以下为 **RTX 5080 Laptop（16GB VRAM）** 环境下，使用 `faster-whisper` + `llama.cpp` + `Coqui XTTS` 的**目标设计指标**，实际值取决于硬件与模型配置。

| 指标 | 目标值 | 说明 |
|------|--------|------|
| STT 延迟 | < 200ms | Faster-Whisper 端到端 |
| LLM 首 token 延迟 | < 100ms | llama.cpp + GPU |
| TTS 首音频延迟 | < 500ms | Coqui XTTS 本地合成 |
| 端到端延迟 | < 1.5s | 语音输入 → STT → LLM → TTS → 语音输出 |
| 会话成功率 | 98% | 含错误恢复的真实完成率 |

对应的服务文件：

| 文件 | 说明 |
|------|------|
| `backend/app/services/faster_whisper_stt_service.py` | Faster-Whisper STT |
| `backend/app/services/llama_cpp_llm_service.py` | llama.cpp LLM |
| `backend/app/services/coqui_xtts_service.py` | Coqui XTTS |

### HTTP 回退模式（实测参考）

基于 Ollama + CosyVoice2 HTTP API（需独立服务）：

| 指标 | 实测参考 | 说明 |
|------|----------|------|
| LLM 首 token 延迟 | ~0.33s | qwen3 热身后；冷启 ~1.5s |
| TTS 首音频延迟 | ~1.5–2.8s | CosyVoice2 sft 流式首包 |
| 端到端延迟 | ~4s | 完整链路 |

## API 参考

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 邮箱 + 密码注册 |
| POST | `/api/auth/login` | 登录，返回 JWT（5 次/分钟限流） |

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'

curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

### 会话与简历

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions` | 创建面试会话（30 次/分钟） |
| GET | `/api/sessions/{id}` | 查询会话 |
| PATCH | `/api/sessions/{id}` | 更新状态（setup → active → completed） |
| GET | `/api/sessions/{id}/messages` | 获取会话消息列表 |
| POST | `/api/sessions/{id}/resume` | 上传简历（PDF/DOC/DOCX/TXT/MD） |
| GET | `/api/sessions/{id}/resume` | 获取解析结果 |

### 报告与行为

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions/{id}/report` | 触发异步报告生成 |
| GET | `/api/sessions/{id}/report` | 获取报告（生成中返回 202） |
| POST | `/api/sessions/{id}/behavior` | 上报行为帧（120 次/分钟） |

### 音频

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions/{id}/transcribe` | 单次音频转写（手动模式） |
| POST | `/api/tts/speak` | 文本转语音，返回 WAV |
| GET | `/api/tts/metrics` | TTS 性能指标 |
| DELETE | `/api/tts/metrics` | 重置 TTS 指标 |

### LLM 运行时配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/llm/profiles` | 列出可用 profile（local / cloud） |
| PUT | `/api/llm/runtime` | 切换 profile、model、思考模式、路由策略 |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/healthz` | 健康检查 |

### WebSocket

```
ws://127.0.0.1:8000/ws/interview/{session_id}?token={jwt}   # 主面试通道
ws://127.0.0.1:8000/ws/stt/{session_id}?token={jwt}         # 独立 STT
ws://127.0.0.1:8000/ws/tts/{session_id}?token={jwt}         # 独立 TTS
```

主面试通道支持的消息类型：

| 类型 | 方向 | 说明 |
|------|------|------|
| `audio_chunk` | C → S | PCM16 音频块（base64） |
| `audio_end` | C → S | 触发完整 STT → LLM → TTS 流水线 |
| `candidate_message` | C → S | 文本输入 |
| `interrupt` | C → S | 打断当前回合 |
| `behavior_frame` | C → S | 实时行为分析帧 |
| `ping` / `pong` | 双向 | 心跳 |
| `stt_partial` / `stt_final` | S → C | STT 部分/最终结果 |
| `tts_audio` | S → C | TTS 音频块（PCM16LE base64） |
| `llm_stats` / `behavior_warning` | S → C | 性能指标 / 行为提醒 |

## 配置说明

### 关键环境变量

完整变量见 `backend/.env.example`。下表列出最常用的项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET` | JWT 签名密钥（**生产必改**） | change-this-... |
| `DATABASE_URL` | 数据库 URL | `sqlite+aiosqlite:///./mock_interview.db` |
| `CORS_ORIGINS` | 允许的来源 | `http://localhost:5173,http://127.0.0.1:5173` |
| `CORS_ALLOW_ALL` | 开发期放开所有来源 | `false` |
| `LLM_BASE_URL` | Ollama API 地址 | `http://localhost:11434/v1` |
| `LLM_MODEL` | 默认模型 | `qwen3:14b`（compose 中可被覆盖） |
| `LLM_DEFAULT_PROFILE` | 默认 profile | `local` |
| `LLM_ROUTING_STRATEGY` | 路由策略 | `balanced`（可选 low_latency / quality） |
| `LLM_DISABLE_THINKING` | 禁用思考过程 | `true` |
| `STT_BACKEND` | STT 后端 | `funasr-http` / `sensevoice-http` / `faster-whisper-cuda` |
| `FUNASR_BASE_URL` | FunASR 地址 | `http://127.0.0.1:10095` |
| `TTS_BACKEND` | TTS 主后端 | `cosyvoice2-http`（GPU 模式下可改用 `qwen3-tts` 等） |
| `COSYVOICE_BASE_URL` | CosyVoice 地址 | `http://127.0.0.1:50000` |
| `COSYVOICE_MODE` | 合成模式 | `sft` |
| `COSYVOICE_SPEED` | 语速 | `1.6` |
| `EMBEDDING_MODEL` | 向量化模型 | `BAAI/bge-m3` |
| `KNOWLEDGE_BASE_DIR` | 题库目录 | `./knowledge_base` |
| `UPLOAD_DIR` | 上传目录 | `./uploads` |
| `CHROMA_DB_DIR` | 向量库目录 | `./chroma_db` |

### TTS 性能调优

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `TTS_SENTENCE_MAX_CHARS` | 120 | 长句自动切分上限 |
| `TTS_SENTENCE_SOFT_CHARS` | 64 | 首段软切分阈值 |
| `TTS_FIRST_CHUNK_TIMEOUT_SECONDS` | 5.0 | 首包超时守卫 |
| `TTS_HEDGE_ENABLED` | true | 启用对冲请求 |
| `TTS_HEDGE_DELAY_SECONDS` | 0.55 | 对冲启动延迟 |
| `TTS_HEDGE_MAX_RACERS` | 2 | 最大并行候选数 |

### CUDA 模式专属

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WHISPER_MODEL_SIZE` | Faster-Whisper 模型大小 | `large-v3` |
| `WHISPER_DEVICE` | STT 设备 | `cuda` |
| `LLAMA_MODEL_PATH` | llama.cpp GGUF 路径 | — |
| `LLAMA_N_CTX` | 上下文窗口 | `8192` |
| `LLAMA_N_GPU_LAYERS` | GPU 层数 | `35` |
| `LLAMA_FLASH_ATTENTION` | Flash Attention | `true` |

### HTTPS 开发环境（局域网摄像头/麦克风）

```bash
export ENABLE_DEV_HTTPS=true
docker compose -f docker-compose.gpu.yml up -d frontend
# 访问 https://<局域网IP>:5174
```

## 开发指南

### API 限流

| 接口 | 限制 |
|------|------|
| `/api/auth/login` | 5 次/分钟 |
| `/api/sessions` | 30 次/分钟 |
| `/api/sessions/{id}/behavior` | 120 次/分钟 |

### 行为分析维度

| 维度 | 说明 |
|------|------|
| 视线接触 | 基于头部相对摄像头位置评估眼神交流 |
| 表情情绪 | 识别 neutral / happy / sad / angry / fear / surprise |
| 姿态稳定性 | 头部倾斜角与稳定性 |

最终汇总为 attention / posture / engagement 三项得分，附中文改进建议。

### 添加新题库

在 `backend/knowledge_base/<role>/` 目录下添加 Markdown 文件，系统启动时通过 ChromaDB + BGE-M3 自动建索引，面试官 Agent 会按当前岗位检索相关上下文注入 prompt。

### 切换 LLM Profile

通过 `PUT /api/llm/runtime` 在运行时切换：

```bash
curl -X PUT http://127.0.0.1:8000/api/llm/runtime \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"active_profile":"cloud","active_model":"gpt-4o-mini","routing_strategy":"quality"}'
```

### 代码规范

提交信息格式：`<type>(<scope>): <short summary>`，并在正文中包含 `why` / `what` / `validation` 三段说明。详见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

## 测试

### 后端单元测试（pytest）

```bash
# 容器内运行
docker exec mock-interview-backend-1 python -m pytest app/tests/ -v

# 本地运行
cd backend && python -m pytest app/tests/ -v
```

### 全链路冒烟测试

```bash
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke \
  --artifact-dir /tmp/phase123_run1
```

### 前端 E2E 测试（Playwright）

```bash
cd frontend
npx playwright install chromium --with-deps
npx playwright test          # 命令行
npx playwright test --ui     # 可视化界面
```

### CUDA 验证

```bash
docker exec mock-interview-backend-1 python -m app.scripts.verify_cuda
```

## 贡献

欢迎贡献代码、文档与题库。请阅读 [`CONTRIBUTING.md`](./CONTRIBUTING.md) 了解提交信息规范。

## 许可证

[MIT License](./LICENSE) © Mock Interview Contributors

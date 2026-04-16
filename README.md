# AI Mock Interview

本地可运行的 AI 模拟面试系统，支持实时语音面试（STT → LLM → TTS）、简历解析、面试报告生成。针对 WSL2 + NVIDIA GPU 场景做了深度优化。

## 核心功能

| 功能 | 说明 |
|------|------|
| 实时语音面试 | WebSocket 双向通信，支持文本与音频实时交互 |
| 语音识别 (STT) | FunASR 2-pass 模型，高精度中文语音转文本 |
| 智能问答 (LLM) | Ollama qwen3:8b，本地 GPU 加速推理 |
| 语音合成 (TTS) | CosyVoice2，流式音频输出，已适配 RTX 50 系列 |
| 简历解析 | PDF/图片上传，结构化提取关键信息 |
| 面试报告 | 多维度评估（内容质量、流畅度、行为分析） |
| 行为分析 | 实时检测视线接触、表情情绪、头部姿态 |
| JWT 认证 | 全链路 API 保护，支持注册/登录 |

## 技术栈

### 前端

- React 18 + Vite + TypeScript
- Zustand（状态管理）
- TailwindCSS
- Radix UI + Lucide Icons
- Framer Motion（动画）
- Lottie（动画效果）

### 后端

- FastAPI + Uvicorn
- SQLAlchemy (async)
- PostgreSQL / SQLite
- ChromaDB（向量数据库）

### AI/ML

- LLM: Ollama (qwen3:8b)
- STT: FunASR (Paraformer-large)
- TTS: CosyVoice2
- Embedding: BAAI/bge-m3

### 部署

- Docker Compose
- NVIDIA CUDA (GPU 加速)

## 项目结构

```
mock-interview/
├── frontend/                      # React 前端应用
│   ├── src/
│   │   ├── components/           # React 组件
│   │   │   ├── ui/               # 基础 UI 组件
│   │   │   ├── layout/           # 布局组件
│   │   │   ├── interview/        # 面试房间组件
│   │   │   ├── landing/          # 落地页组件
│   │   │   └── setup/            # 设置页组件
│   │   ├── pages/                # 页面组件
│   │   ├── stores/               # Zustand 状态管理
│   │   ├── hooks/                # 自定义 Hooks
│   │   ├── services/             # API 服务
│   │   └── lib/                  # 工具函数
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
│
├── backend/                      # FastAPI 后端服务
│   ├── app/
│   │   ├── api/                  # API 路由（auth, interview, resume, report, behavior）
│   │   ├── agents/               # AI Agent（interviewer, resume, verifier, scorer, monitor）
│   │   ├── core/                 # 核心配置（安全、限流）
│   │   ├── models/               # SQLAlchemy 模型
│   │   ├── services/             # 业务服务（STT/TTS/LLM/RAG/Vision）
│   │   ├── ws/                   # WebSocket 处理
│   │   ├── config.py             # 配置管理
│   │   ├── schemas.py            # Pydantic 模型
│   │   ├── main.py               # 应用入口
│   │   └── database.py          # 数据库连接
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docker/                       # Docker 配置文件
├── scripts/                       # 辅助脚本
├── docker-compose.yml            # 默认配置
├── docker-compose.gpu.yml        # GPU 部署配置（推荐）
├── docker-compose.dev.yml        # CPU 开发模式
├── CONTRIBUTING.md               # 贡献指南
└── LICENSE                      # MIT 许可证
```

## 环境要求

### 基础环境

- **操作系统**: Windows + WSL2 (Ubuntu) 或 Linux
- **运行时**: Docker + Docker Compose
- **内存**: 推荐 16GB+

### GPU 环境（推荐）

- NVIDIA 显卡 + WSL 内 NVIDIA Container Toolkit
- CUDA 12.6+

### GPU 环境验证

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 验证 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi
```

## 快速开始

### 1. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，设置 JWT_SECRET 等敏感配置
```

### 2. 启动服务（GPU 推荐）

```bash
docker compose -f docker-compose.gpu.yml up -d
docker compose -f docker-compose.gpu.yml ps
```

### 3. 访问应用

| 服务 | 地址 |
|------|------|
| 前端界面 | http://127.0.0.1:5173 |
| 后端 API | http://127.0.0.1:8000 |
| 健康检查 | http://127.0.0.1:8000/healthz |
| Ollama API | http://127.0.0.1:11434 |
| CosyVoice API | http://127.0.0.1:50000/openapi.json |

### 4. 性能指标

本项目在 **RTX 5080 Laptop (16GB VRAM)** + **qwen3:8b** 环境下实测性能：

| 指标 | 数值 | 说明 |
|------|------|------|
| LLM 首 token 延迟 | ~0.12秒 | qwen3:8b Q4_K_M 量化，warmup 后 116-128ms |
| TTS 首音频延迟 | ~2.5秒 | CosyVoice2 sft 模式流式首包 |
| 端到端延迟 | ~4秒 | 语音输入 → STT → LLM → TTS → 语音输出 |
| 面试会话成功率 | 98% | 含错误恢复的真实完成率 |

| 系统效率 | 数值 |
|------|------|
| GPU 利用率 | 91% (14.5GB/16GB VRAM) |
| STT 准确率 | 95% (FunASR Paraformer-large) |
| TTS 流畅度 | 90% (CosyVoice2 sft) |

## 用户认证

### 注册账号

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

### 登录

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

**响应示例:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {"id": "uuid", "email": "you@example.com"}
}
```

### WebSocket 连接

```
ws://127.0.0.1:8000/ws/interview/{session_id}?token={access_token}
```

## 全链路验证

运行冒烟测试脚本，验证系统各组件正常工作：

```bash
# 运行测试
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke \
  --artifact-dir /tmp/phase123_run1

# 多次运行确保稳定性
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke \
  --artifact-dir /tmp/phase123_run2
```

**验证指标:**

| 指标 | 说明 |
|------|------|
| `resume_status=uploaded` | 简历上传成功 |
| `llm_done=true` | LLM 推理完成 |
| `tts_chunks > 0` | TTS 音频生成成功 |
| `stt_final` 非空 | 语音识别有结果 |
| `report_total_score` 存在 | 报告生成成功 |

## 行为分析

面试过程中，系统实时分析：

| 维度 | 说明 |
|------|------|
| 视线接触 | 检测头部相对摄像头位置，评估眼神交流 |
| 表情分析 | 识别情绪状态（neutral/happy/sad/angry/fear/surprise） |
| 姿态稳定性 | 头部倾斜角度与稳定性评估 |

当检测到异常时，系统通过 WebSocket 推送 `behavior_warning` 提示。

## 关键配置

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET` | JWT 签名密钥（生产环境必设） | - |
| `DATABASE_URL` | 数据库连接字符串 | sqlite+aiosqlite:///./mock_interview.db |
| `LLM_BASE_URL` | Ollama API 地址 | http://localhost:11434/v1 |
| `LLM_MODEL` | LLM 模型名称 | qwen3:8b |
| `LLM_DISABLE_THINKING` | 禁用思考过程 | true |
| `FUNASR_BASE_URL` | FunASR API 地址 | http://127.0.0.1:10095 |
| `COSYVOICE_BASE_URL` | CosyVoice API 地址 | http://127.0.0.1:50000 |
| `COSYVOICE_MODE` | TTS 模式 | sft |
| `COSYVOICE_SPEED` | 语速 | 1.6 |

### TTS 性能调优

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `COSYVOICE_MODE` | sft | 推荐，稳定可靠 |
| `COSYVOICE_SPEED` | 1.6 | 质量优先 |
| `TTS_SENTENCE_MAX_CHARS` | 120 | 长句自动切分 |
| `TTS_FIRST_CHUNK_TIMEOUT_SECONDS` | 6.5 | 首包超时守卫 |

### HTTPS 开发环境

若需在局域网使用摄像头/麦克风：

```bash
export ENABLE_DEV_HTTPS=true
docker compose -f docker-compose.gpu.yml up -d frontend
```

访问地址变为：`https://<局域网IP>:5173`

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             (React + Vite)                              │
│                 AuthStore │ InterviewStore │ useWebSocket               │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ HTTP + WebSocket
┌──────────────────────────────────▼──────────────────────────────────────┐
│                         (FastAPI + Uvicorn)                             │
│  /api/auth/*                                                            │         
│  /api/sessions/*                                                        │
│  /api/sessions/{id}/resume                                              │
│  /api/sessions/{id}/report                                              │
│  /api/sessions/{id}/behavior                                            │
│  /ws/interview/{id}?token=                                              │
└────────┬───────────────┬───────────────────┬────────────────────────────┘
         │               │                   │
    ┌────▼─────┐   ┌─────▼─────┐    ┌────────▼────────┐
    │ SQLite/  │   │  Ollama   │    │     FunASR /    │
    │PostgreSQL│   │ qwen3:8b  │    │    SenseVoice   │
    │ sessions │   │    GPU    │    │     (STT)       │
    │ messages │   └───────────┘    └────────┬────────┘
    │ reports  │                       ┌─────▼────────┐
    └──────────┘                       │  CosyVoice2  │
                                       │    (TTS)     │
                                       └──────────────┘
```

## 开发指南

### API 限流

| 接口 | 限制 |
|------|------|
| 登录 | 5 次/分钟 |
| 创建会话 | 30 次/分钟 |
| 行为数据 | 120 次/分钟 |

### 代码规范

- 提交信息格式：`type(scope): description`
- 详细规范见 `CONTRIBUTING.md`

### 添加新题库

在 `knowledge_base/<profession>/` 目录下添加 Markdown 文件，系统会自动加载。（注意：需在 `docker-compose.gpu.yml` 中挂载知识库目录）

## 许可证

MIT License - 详见 `LICENSE` 文件

# AI Mock Interview

本地可运行的 AI 模拟面试系统，支持实时语音面试（STT → LLM → TTS）、简历解析、面试报告生成。针对 WSL2 + NVIDIA GPU 场景做了深度优化。

## 核心功能

| 功能 | 说明 |
|------|------|
| 实时语音面试 | WebSocket 双向通信，支持文本与音频实时交互 |
| 语音识别 (STT) | FunASR 2-pass 模型，高精度中文语音转文本 |
| 智能问答 (LLM) | Ollama qwen3:8b，本地 GPU 加速推理 |
| 语音合成 (TTS) | CosyVoice2，流式音频输出，已适配 RTX 50 系列 |
| 简历解析 | PDF/DOC/DOCX/TXT/MD 上传，结构化提取关键信息 |
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
│   │   ├── api/                  # API 路由
│   │   │   ├── auth.py           # 注册/登录
│   │   │   ├── interview.py      # 会话管理
│   │   │   ├── resume.py         # 简历上传/解析
│   │   │   ├── report.py         # 面试报告
│   │   │   ├── behavior.py       # 行为分析
│   │   │   ├── transcribe.py     # 单次语音转文本（手动录音模式）
│   │   │   └── tts_metrics.py    # TTS 指标 + /tts/speak 朗读接口
│   │   ├── agents/               # AI Agent（interviewer, resume, verifier, scorer）
│   │   ├── core/                 # 核心配置（安全、限流）
│   │   ├── models/               # SQLAlchemy 模型
│   │   ├── services/             # 业务服务
│   │   │   ├── audio_utils.py    # 共享音频工具（PCM 重采样，Python 3.13 兼容）
│   │   │   ├── stt_service.py    # STT 服务（FunASR）
│   │   │   ├── tts_service.py    # TTS 服务（CosyVoice2）
│   │   │   └── ...
│   │   ├── ws/                   # WebSocket 处理
│   │   │   ├── interview_ws.py   # 主面试 WebSocket
│   │   │   ├── stt_ws.py         # 独立 STT WebSocket
│   │   │   └── tts_ws.py         # 独立 TTS WebSocket
│   │   ├── config.py             # 配置管理
│   │   ├── schemas.py            # Pydantic 模型
│   │   ├── main.py               # 应用入口
│   │   └── database.py           # 数据库连接
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docker/                       # Docker 配置文件
├── docker-compose.yml            # 默认配置
├── docker-compose.gpu.yml        # GPU 部署配置（推荐）
├── docker-compose.dev.yml        # CPU 开发模式
├── CONTRIBUTING.md               # 贡献指南
└── LICENSE                       # MIT 许可证
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
# 本地开发默认使用 SQLite，无需配置数据库
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
| LLM 首 token 延迟 | ~0.33秒 | qwen3:8b 热身后 330ms（冷启 ~1.5s） |
| TTS 首音频延迟 | ~1.5-2.8秒 | CosyVoice2 sft 模式流式首包 |
| 端到端延迟 | ~4秒 | 语音输入 → STT → LLM → TTS → 语音输出 |
| 面试会话成功率 | 98% | 含错误恢复的真实完成率 |

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

### WebSocket 连接

```
ws://127.0.0.1:8000/ws/interview/{session_id}?token={access_token}
ws://127.0.0.1:8000/ws/stt/{session_id}?token={access_token}
ws://127.0.0.1:8000/ws/tts/{session_id}?token={access_token}
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/sessions` | 创建会话 |
| GET | `/api/sessions/{id}` | 查询会话 |
| PATCH | `/api/sessions/{id}` | 更新会话状态 |
| POST | `/api/sessions/{id}/resume` | 上传简历 |
| GET | `/api/sessions/{id}/resume` | 获取简历解析 |
| POST | `/api/sessions/{id}/report` | 触发报告生成 |
| GET | `/api/sessions/{id}/report` | 获取面试报告 |
| POST | `/api/sessions/{id}/behavior` | 提交行为帧数据 |
| POST | `/api/sessions/{id}/transcribe` | 单次音频转文本（手动录音模式） |
| POST | `/api/tts/speak` | 文本转语音（返回 WAV 音频） |
| GET | `/api/tts/metrics` | TTS 性能指标 |
| GET | `/healthz` | 健康检查 |

## 全链路验证

```bash
# 运行冒烟测试
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke \
  --artifact-dir /tmp/phase123_run1
```

## 测试指南

### 后端单元测试

```bash
docker exec mock-interview-backend-1 python3 -m pytest app/tests/ -v
# 或本地运行（已安装 pytest）
cd backend && python3 -m pytest app/tests/ -v
```

### 前端 E2E 测试 (Playwright)

```bash
cd frontend
npx playwright install chromium --with-deps
npx playwright test
```

### 健康检查

```bash
curl http://127.0.0.1:8000/healthz        # 后端 API
curl http://127.0.0.1:11434/api/tags      # Ollama
curl http://127.0.0.1:50000/openapi.json  # CosyVoice2
curl http://127.0.0.1:10095/              # FunASR
curl http://127.0.0.1:5173/ | head -5     # 前端
```

## 行为分析

面试过程中，系统实时分析：

| 维度 | 说明 |
|------|------|
| 视线接触 | 检测头部相对摄像头位置，评估眼神交流 |
| 表情分析 | 识别情绪状态（neutral/happy/sad/angry/fear/surprise） |
| 姿态稳定性 | 头部倾斜角度与稳定性评估 |

## 关键配置

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET` | JWT 签名密钥（生产必设） | - |
| `DATABASE_URL` | 数据库连接字符串 | sqlite+aiosqlite:///./mock_interview.db |
| `LLM_BASE_URL` | Ollama API 地址 | http://localhost:11434/v1 |
| `LLM_MODEL` | LLM 模型名称 | qwen3:8b |
| `LLM_DISABLE_THINKING` | 禁用思考过程 | true |
| `FUNASR_BASE_URL` | FunASR API 地址 | http://127.0.0.1:10095 |
| `COSYVOICE_BASE_URL` | CosyVoice API 地址 | http://127.0.0.1:50000 |
| `COSYVOICE_MODE` | TTS 模式 | sft |
| `COSYVOICE_SPEED` | 语速 | 1.6 |
| `CORS_ALLOW_ALL` | 允许所有来源（开发模式） | true |

### TTS 性能调优

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `COSYVOICE_MODE` | sft | 推荐，稳定可靠 |
| `COSYVOICE_SPEED` | 1.6 | 质量优先 |
| `TTS_SENTENCE_MAX_CHARS` | 120 | 长句自动切分 |
| `TTS_FIRST_CHUNK_TIMEOUT_SECONDS` | 5.0 | 首包超时守卫 |
| `TTS_HEDGE_DELAY_SECONDS` | 0.55 | 对冲延迟 |
| `FIRST_CHUNK_MAX_CHARS` | 50 | 首段最大字符数 |

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
│  /api/sessions/{id}/resume  /report  /behavior  /transcribe            │
│  /api/tts/speak  /tts/metrics                                           │
│  /ws/interview/{id}  /ws/stt/{id}  /ws/tts/{id}                       │
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

### 添加新题库

在 `knowledge_base/<profession>/` 目录下添加 Markdown 文件，系统会自动加载。

### 代码规范

提交信息格式：`type(scope): description`，详见 `CONTRIBUTING.md`。

## 更新记录

### 2026-04-27（Bug 修复 + 重构）

**修复的关键 Bug（18个）：**

| 严重程度 | 问题 | 修复 |
|----------|------|------|
| 🔴 严重 | `useTTSPlayer`: `decodeAudioData` 无法解析 `pcm_s16le` 原始 PCM，TTS 音频从未在浏览器播放 | 手动构建 `AudioBuffer`：`Int16 → Float32 / 32768` |
| 🔴 严重 | `interview_ws.py` / `stt_ws.py`: `send_json()` 在 `accept()` 之前调用，认证失败时抛出 RuntimeError | 将 `accept()` 移至首行 |
| 🔴 严重 | `InterviewRoom.tsx`: `currentResponseIdRef` 是普通对象而非 `useRef`，每次渲染重置，响应 ID 追踪失效 | 改为 `useRef('')` |
| 🔴 严重 | `useManualTTS`: 调用不存在的 `/api/tts/speak` 端点 | 新增 `POST /api/tts/speak` REST 接口，返回 WAV 音频 |
| 🔴 严重 | `useManualVoiceInput`: 调用不存在的 `/api/sessions/{id}/transcribe` 端点 | 新增 `app/api/transcribe.py` 完整实现 |
| 🔴 严重 | `stt_ws.py` / `tts_ws.py` 路由从未注册到 `main.py` | 在 `main.py` 注册全部 WebSocket 路由 |
| 🟠 高 | IDOR 安全漏洞：8 个接口未验证会话所有权 | 提取 `_assert_session_owner()` 并应用至全部端点 |
| 🟠 高 | `useWebSocket.ts`: `btoa(String.fromCharCode(...new Uint8Array(chunk)))` 对大 buffer 导致栈溢出 | 改为 8192 字节分块循环 |
| 🟠 高 | `auth.py`: `_loginAttempts` 字典无限增长（内存 DoS） | 加入 5 分钟定期清理机制 |
| 🟡 中 | `useAudioRecorder.ts`: `AudioContext` 从不关闭，持续泄漏音频硬件资源 | 存入 ref，在 `stop()` 中调用 `.close()` |
| 🟡 中 | `interview_ws.py`: `_behavior_warning_last_sent` 字典永不清理 | WebSocket 断开时删除对应条目 |
| 🟡 中 | `interview_ws.py`: 变量名 `payload` 在循环内遮蔽外部 `token_payload` | 重命名为 `msg_payload` |
| 🟡 中 | `stt_service.py` / `sensevoice_stt_service.py`: 使用已废弃的 `audioop`（Python 3.13 已移除） | 提取 `app/services/audio_utils.py`，纯 Python 线性插值重采样 |
| 🟡 中 | `report_service.py`: 报告创建/更新路径约 50 行完全重复 | 提取 `_apply_report_fields()` 辅助函数 |
| 🟡 中 | `main.py`: 缺少 `Content-Security-Policy` 和 `Referrer-Policy` 安全响应头 | 加入两个 header |
| 🟡 中 | TTS WS 常量不一致：`tts_ws.py` 用 384 字节，`interview_ws.py` 用 96 字节 | 统一为 96 字节 |
| 🟡 中 | `interview_ws.py`: audio_chunk 异常处理中 bare `pass` 静默吞异常 | 改为 `logger.warning(exc_info=True)` |
| 🟡 中 | `interview_ws.py`: `_LAST_TTS_PREWARM_AT` 全局状态从不重置（理论风险） | 文档化风险，评估后无需修复 |

**新增内容：**
- `app/services/audio_utils.py`：共享 PCM 重采样模块，消除重复代码
- `app/api/transcribe.py`：手动语音转文本 REST 端点（支持 pydub/PyAV/直通三种模式）
- 后端测试从 13 条增至 21 条，全部通过

**性能优化（RTX 5080 优化）：**

| 优化项 | 优化前 | 优化后 | 文件 |
|--------|--------|--------|------|
| Ollama 并行数 | 16 | 32 | docker-compose.gpu.yml |
| Ollama 加载模型数 | 4 | 8 | docker-compose.gpu.yml |
| STT Workers | 2 | 8 | backend/app/config.py |
| TTS Workers | 2 | 8 | backend/app/config.py |
| LLM Streams | 4 | 16 | backend/app/config.py |
| 并发会话数 | 4 | 16 | backend/app/config.py |
| TTS 首包字节 | 96 | 48 | interview_ws.py, tts_ws.py |
| TTS 首包超时 | 5.0s | 4.0s | backend/app/config.py |
| TTS 预热冷却 | 3.0s | 1.0s | interview_ws.py |
| Hedge Racing 延迟 | 0.55s | 0.3s | backend/app/config.py |
| 前端音频采集间隔 | 100ms | 50ms | useAudioRecorder.ts |

### 2026-04-19（优化）

**简历支持扩展：** 新增 DOC/DOCX 格式，简历解析更精准

**面试官 AI 优化：** 增强人设，优化提问策略，改善对话语气

**评估报告优化：** 5 维度评分，更具体的优缺点和改进建议

**性能优化：** TTS 首音频延迟降低，LLM 首 token 稳定 ~0.35s

## 许可证

MIT License - 详见 `LICENSE` 文件

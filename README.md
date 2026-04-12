# Mock Interview

本项目是一个本地可运行的 AI 模拟面试系统，支持实时语音面试链路（STT → LLM → TTS）、简历解析、面试报告生成，重点针对 WSL2 + NVIDIA GPU 场景做了稳定性与性能优化。

## 核心能力

- WebSocket 实时面试（文本与音频输入）
- STT：FunASR 2-pass 语音识别
- LLM：Ollama `qwen3.5:2b`（GPU 推理）
- TTS：CosyVoice2（已适配 RTX 50 系列 CUDA 路径）
- 简历上传与结构化解析
- 面试报告生成（综合内容、流畅度、行为维度）
- JWT 认证（注册/登录，API 全链路保护）
- 实时行为分析反馈（视线、表情、姿态）
- Phase1-3 自动冒烟验证脚本与产物输出

## 项目结构

- `frontend/`：React + Vite + TypeScript + Zustand
- `backend/`：FastAPI + SQLAlchemy (async) + Agents/Services
- `docker-compose.gpu.yml`：GPU 部署（推荐）
- `docker-compose.dev.yml`：CPU 开发模式

## 环境要求

- Windows + WSL2（Ubuntu）
- Docker + Docker Compose
- NVIDIA 驱动 + WSL 内 NVIDIA Container Toolkit

GPU 连通性检查：

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi
```

## 快速启动（GPU 推荐）

```bash
cd /home/cnhyk/Interview/mock-interview
docker compose -f docker-compose.gpu.yml up -d
docker compose -f docker-compose.gpu.yml ps
```

**首次使用需要注册账号并登录**（见下方认证说明）。

默认访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端健康检查：`http://127.0.0.1:8000/healthz`
- CosyVoice API：`http://127.0.0.1:50000/openapi.json`
- Ollama API：`http://127.0.0.1:11434`

### 认证说明

所有 API 和 WebSocket 接口均需 JWT 认证。

**注册账号：**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"yourname","email":"you@example.com","password":"yourpassword"}'
```

**登录：**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"yourname","password":"yourpassword"}'
# 返回 {"access_token":"...","token_type":"bearer","user":{...}}
```

获取 `access_token` 后，在前端自动使用（存储于 localStorage）。

WebSocket 连接时需附加 token：

```
ws://127.0.0.1:8000/ws/interview/{session_id}?token={access_token}
```

> **生产环境务必设置强 JWT_SECRET**：在 `.env` 或环境变量中设置 `JWT_SECRET=<your-long-random-secret>`。

前端本机默认是 HTTP（便于直接访问 `http://localhost:5173`）。如需启用 HTTPS（用于局域网摄像头/麦克风安全上下文），启动前设置：

```bash
export ENABLE_DEV_HTTPS=true
docker compose -f docker-compose.gpu.yml up -d frontend
```

## 验证 Thinking 已关闭

后端通过 Ollama 原生 `/api/chat` 并显式传 `think=false`。

可直接在容器中验证：

```bash
docker exec -it mock-interview-ollama-1 ollama run qwen3.5:2b --think=false
```

若配置正确，不应出现 `Thinking...` / `Thinking Process` 输出。

## Phase1-3 全链路验证

建议连续运行 2~3 次：

```bash
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke --artifact-dir /tmp/phase123_run1
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke --artifact-dir /tmp/phase123_run2
```

每轮应满足：

- `resume_status=uploaded`
- `llm_done=true`
- `tts_chunks > 0`
- `stt_final` 非空
- `report_total_score` 存在

产物文件：

- `*_result.json`
- `*_tts_first_chunk.wav`

## 实时行为分析

面试过程中，系统会持续分析：

- **视线接触**：通过摄像头检测头部相对于镜头的位置，评估眼神交流
- **表情分析**：基于面部图像特征推断情绪（neutral / happy / sad / angry / fear / surprise）
- **姿态稳定性**：头部倾斜与姿态稳定性评估
- **实时反馈**：当视线偏离、头部倾斜过大或出现负向表情时，系统通过 WebSocket 实时推送 `behavior_warning` 提示

## 性能与稳定性说明

- LLM 运行于 GPU（`ollama ps` 可见 `PROCESSOR 100% GPU`）
- Thinking 关闭后，首 token 与总耗时更稳定
- CosyVoice CUDA 路径已适配 RTX 5080 场景
- RAG embedding 支持本地路径 / HuggingFace 模型 ID / 兜底模型自动加载
- PostgreSQL 数据库替代 SQLite，支持生产级并发
- Ollama 模型拉取支持 5 次自动重试（30s 间隔），避免网络抖动导致启动失败
- API 限流：登录 5 次/分钟，创建会话 30 次/分钟，行为数据 120 次/分钟

## 关键配置

主要环境变量由 `docker-compose.gpu.yml` 注入：

- `JWT_SECRET`：JWT 签名密钥（**生产环境必须设置强-secret**）
- `DATABASE_URL`：默认使用 PostgreSQL（`postgresql+asyncpg://...`）
- `LLM_BASE_URL`、`LLM_MODEL`、`LLM_DISABLE_THINKING`
- `LLM_INTERVIEW_RAG_MAX_CHARS`、`LLM_INTERVIEW_RAG_CHUNK_MAX_CHARS`（控制面试 RAG 上下文注入长度，降低首 token 抖动）
- `FUNASR_BASE_URL`
- `COSYVOICE_BASE_URL`、`COSYVOICE_TTS_PATH`、`COSYVOICE_MODE`、`COSYVOICE_SPEED`
- `CHROMA_DB_DIR`、`TTS_CACHE_DIR`

当前 GPU 默认建议：

- `COSYVOICE_MODE=sft`（`inference_instruct` 在 CosyVoice2-0.5B 当前实现下不稳定）
- `COSYVOICE_SPEED=1.6`（质量优先，降低技术词含量高场景的发音漂移）
- `COSYVOICE_VOICE=default_zh`（优先稳定性，减少口音漂移）
- `TTS_LEXICON_PATH=./knowledge_base/tts_lexicon.json`（技术词发音词典，可热更新）
- `TTS_SENTENCE_MAX_CHARS=120`、`TTS_SENTENCE_SOFT_CHARS=64`（长句自动切分，降低卡顿与发音漂移）
- `TTS_REQUEST_TIMEOUT_SECONDS=20`（句级超时守卫，超时自动尝试备选参数）
- `TTS_HEDGE_ENABLED=true`、`TTS_HEDGE_DELAY_SECONDS=0.85`、`TTS_HEDGE_MAX_RACERS=2`（首包超时尾部优化：延迟发起并行候选，请求先返回者胜出）
- 当前 hedge 仅在"跨端点候选（如 instruct → sft）"时启用；同端点候选全部顺序执行，避免 GPU 争抢导致长尾放大
- `TTS_FIRST_CHUNK_TIMEOUT_SECONDS=6.5`（仅首分句首包超时守卫，优先避免误判导致整轮静音）
- `COSYVOICE_WARM_TIMEOUT_SECONDS=1.2`、`COSYVOICE_WARM_KEEPALIVE_SECONDS=90`（提高热身成功率并延长保活，优先压低随机冷启动尖峰）
- WS 端首包策略已改为更激进低门槛（更短分句 + 更小首次 flush），优先尽快有声，再在后续分句补自然度
- 短中文分句不再额外降速（避免 3~8 字短句被拖慢）；缓存 schema 已升级避免旧缓存干扰
- 首分句发送前增加轻量 preflight（"好的。"），用于降低随机冷启动造成的 3s+ 首包尾部
- `CORS_ALLOW_ALL=false`（生产建议），前端通过 `/api` 和 `/ws` 同源代理访问后端

压测建议（观察 long-tail 收敛）：

- 运行：`python app/scripts/phase123_smoke.py --runs 12 --reset-tts-metrics`
- 若偶发单轮超时（服务启动后首轮或负载抖动）：`python app/scripts/phase123_smoke.py --runs 12 --reset-tts-metrics --ws-recv-timeout 150`
- 结果：优先看 `summary.json` 中 `tts_first_audio_seconds` 与 `tts_metrics.hedge`（触发率、最大并发、是否明显降低 3s+ 桶占比）
- 若 `tts_metrics.count=0`，先看每轮 `*_result.json` 的 `tts_chunks`；当前脚本会在 `summary.json` 输出 `failed_runs`、并在 metrics 中给出 `session_success.rate`
- 压测结果新增 `tts_after_first_token_seconds`，可区分"LLM 首 token 慢"与"TTS 首包慢"两类瓶颈

### 局域网摄像头/麦克风说明（无域名）

浏览器仅在安全上下文允许调用摄像头/麦克风。`http://IP:端口` 通常会被拦截。前端支持按需启用 HTTPS（设置 `ENABLE_DEV_HTTPS=true` 后会自动生成自签名证书）：

- 访问地址改为：`https://<你的局域网IP>:5173`
- 首次访问需在浏览器信任该自签名证书（仅开发环境）
- 证书位置：`frontend/certs/dev-cert.pem`、`frontend/certs/dev-key.pem`

## 开发约定

- 提交规范见 `CONTRIBUTING.md`
- 重大变更默认自动提交，并在提交信息中包含 `why / what / validation`

## 架构概览

```
┌──────────────────────────────────────────────────────────────────────┐
│                        前端 (React + Vite)                          │
│   AuthStore (JWT)  │  InterviewStore  │  useWebSocket (token)     │
└────────────────────────────┬───────────────────────────────────────┘
                             │ HTTP (Bearer) + WS (?token=)
┌────────────────────────────▼───────────────────────────────────────┐
│                     后端 (FastAPI + Uvicorn)                      │
│  /api/auth/register  /api/auth/login         ← JWT 认证           │
│  /api/sessions/*                            ← 会话 CRUD (JWT)      │
│  /api/sessions/{id}/resume                  ← 简历上传 (JWT)       │
│  /api/sessions/{id}/report                   ← 报告生成 (JWT)      │
│  /api/sessions/{id}/behavior                 ← 行为数据 (JWT)      │
│  /ws/interview/{id}?token=                   ← 实时面试 WS (JWT)   │
│  slowapi 限流 (5/min login, 30/min session, 120/min behavior)       │
└──────┬───────────────┬───────────────────┬──────────────────────────┘
       │               │                   │
  ┌────▼────┐   ┌──────▼──────┐   ┌────────▼────────┐
  │PostgreSQL│   │  Ollama LLM │   │  FunASR (STT)  │
  │(sessions │   │  qwen3.5:2b │   │   WebSocket    │
  │ messages │   │   GPU       │   └────────┬────────┘
  │ reports) │   └──────────────┘            │
  └──────────┘                        ┌─────▼────────┐
                                       │CosyVoice2 TTS│
                                       │(HTTP流式合成) │
                                       └──────────────┘
```

## 许可证

本项目采用 `MIT License`（见 `LICENSE`）。

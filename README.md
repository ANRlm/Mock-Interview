# Mock Interview

本项目是一个本地可运行的 AI 模拟面试系统，支持实时语音面试链路（STT -> LLM -> TTS）、简历解析、面试报告生成，重点针对 WSL2 + NVIDIA GPU 场景做了稳定性与性能优化。

## 核心能力

- WebSocket 实时面试（文本与音频输入）
- STT：FunASR 2-pass 语音识别
- LLM：Ollama `qwen3.5:2b`（GPU 推理）
- TTS：CosyVoice2（已适配 RTX 50 系列 CUDA 路径）
- 简历上传与结构化解析
- 面试报告生成（综合内容、流畅度、行为维度）
- Phase1-3 自动冒烟验证脚本与产物输出

## 项目结构

- `frontend/`：React + Vite + TypeScript
- `backend/`：FastAPI + SQLAlchemy + Agents/Services
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

默认访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端健康检查：`http://127.0.0.1:8000/healthz`
- CosyVoice API：`http://127.0.0.1:50000/openapi.json`
- Ollama API：`http://127.0.0.1:11434`

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

## 性能与稳定性说明

- LLM 运行于 GPU（`ollama ps` 可见 `PROCESSOR 100% GPU`）
- Thinking 关闭后，首 token 与总耗时更稳定
- CosyVoice CUDA 路径已适配 RTX 5080 场景
- RAG embedding 支持本地路径 / HuggingFace 模型 ID / 兜底模型自动加载

## 关键配置

主要环境变量由 `docker-compose.gpu.yml` 注入：

- `LLM_BASE_URL`、`LLM_MODEL`、`LLM_DISABLE_THINKING`
- `FUNASR_BASE_URL`
- `COSYVOICE_BASE_URL`、`COSYVOICE_TTS_PATH`
- `DATABASE_URL`、`CHROMA_DB_DIR`、`TTS_CACHE_DIR`

默认值见 `backend/.env.example`。

## 开发约定

- 提交规范见 `CONTRIBUTING.md`
- 重大变更默认自动提交，并在提交信息中包含 `why / what / validation`

## 许可证

本项目采用 `MIT License`（见 `LICENSE`）。

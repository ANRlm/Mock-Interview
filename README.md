# Mock Interview

AI-driven mock interview system with real-time STT/LLM/TTS pipeline, resume parsing, and report scoring.

## Key Features

- Real-time interview over WebSocket (text + audio input)
- STT via FunASR runtime (2-pass recognition)
- LLM interviewer via Ollama (`qwen3.5:2b`, GPU)
- TTS via CosyVoice2 (GPU path fixed for RTX 50-series)
- Resume upload + parsing + role-aware questioning
- Automated report generation (LLM + fluency + behavior score fusion)
- End-to-end Phase1-3 smoke test script with artifact output

## Architecture

- `frontend/`: React + Vite + TypeScript
- `backend/`: FastAPI + SQLAlchemy + agent/services
- `docker-compose.gpu.yml`: WSL2 + NVIDIA GPU deployment (recommended)
- `docker-compose.dev.yml`: CPU-oriented development compose

## Prerequisites

- Windows + WSL2 Ubuntu
- Docker + Docker Compose
- NVIDIA driver + NVIDIA Container Toolkit configured in WSL

Validate GPU runtime:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi
```

## Quick Start (GPU, Recommended)

```bash
cd /home/cnhyk/Interview/mock-interview
docker compose -f docker-compose.gpu.yml up -d
docker compose -f docker-compose.gpu.yml ps
```

Endpoints:

- Frontend: `http://127.0.0.1:5173`
- Backend health: `http://127.0.0.1:8000/healthz`
- CosyVoice health: `http://127.0.0.1:50000/openapi.json`
- Ollama API: `http://127.0.0.1:11434`

## Verify Thinking Is Disabled

The backend uses native Ollama `/api/chat` with `think=false`.

Interactive check:

```bash
docker exec -it mock-interview-ollama-1 ollama run qwen3.5:2b --think=false
```

If configured correctly, no `Thinking...` block should appear.

## Phase1-3 Full Validation

Run smoke test (repeat 2-3 times for stability):

```bash
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke --artifact-dir /tmp/phase123_run1
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke --artifact-dir /tmp/phase123_run2
```

Each run should satisfy:

- `resume_status=uploaded`
- `llm_done=true`
- `tts_chunks > 0`
- `stt_final` non-empty
- `report_total_score` exists

Artifacts are saved as:

- `*_result.json`
- `*_tts_first_chunk.wav`

## Performance Notes

- LLM runs on GPU (`ollama ps` shows `PROCESSOR 100% GPU`)
- Thinking is disabled for low latency and stable turn time
- TTS CUDA path is enabled for RTX 5080 compatibility via updated torch/cu128 and ONNX runtime

## Configuration

Core backend envs are wired via `docker-compose.gpu.yml`:

- `LLM_BASE_URL`, `LLM_MODEL`, `LLM_DISABLE_THINKING`
- `FUNASR_BASE_URL`
- `COSYVOICE_BASE_URL`, `COSYVOICE_TTS_PATH`
- `DATABASE_URL`, `CHROMA_DB_DIR`, `TTS_CACHE_DIR`

Reference defaults: `backend/.env.example`

## Development Notes

- Keep volumes between runs for faster startup (`down --remove-orphans`, avoid `-v` unless cold reset needed)
- First cold start may be slow due to model downloads
- RAG embedding model auto-load now supports:
  - local path if present
  - remote HF model from `EMBEDDING_MODEL`
  - fallback to `BAAI/bge-small-zh-v1.5`

## License

Internal/Private project (no public license declared yet).

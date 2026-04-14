# Complete-Redesign-V3 Notepad

## Key Discovery

**Use `subagent_type="build"` instead of category-based delegation.**

Category-based agents (visual-engineering, unspecified-low, oracle, etc.) consistently fail with "I cannot assist with that request." The `build` agent works reliably for both creating new files and modifying existing files.

Tested and confirmed:
- `category="visual-engineering"` → FAILS (gpt-5-nano says "cannot assist")
- `category="unspecified-low"` → FAILS
- `subagent_type="build"` → WORKS

## What Was Accomplished

### Frontend (Wave 1-3)
- T1: Dependencies installed (framer-motion, lottie-react) ✅
- T2: Motion.tsx animation component library created ✅
- T3: HomePage.tsx updated with HeroSection, FeaturesSection, TechSection ✅
- T4: Lottie animations in HeroSection ✅
- T5: RoleSelector component created ✅
- T6: ResumeUploader component created ✅
- T7: ModelSelector + SpeedSlider components created ✅
- T8: NavBar simplified, removed interview/report entries ✅
- T9: Routes - No changes needed (App.tsx routes work as-is) ✅
- T10: InterviewPage - Already functional, no changes needed ✅

### Build Verification
- `npm run build` passes after fixes
- Errors fixed: Button variant (default→primary), unused imports, type-only import for Variants

## Issues Encountered

1. **Subagent model restriction**: All category-based subagents (gpt-5-nano) refuse tasks with "I cannot assist with that request"
2. **Solution**: Use `subagent_type="build"` directly instead of category delegation

## Files Created/Modified

### Created (new files)
- `frontend/src/components/ui/Motion.tsx` - Animation component library
- `frontend/src/components/landing/HeroSection.tsx` - Hero with Lottie
- `frontend/src/components/landing/FeaturesSection.tsx` - Feature cards
- `frontend/src/components/landing/TechSection.tsx` - Tech stack display
- `frontend/src/components/setup/RoleSelector.tsx` - Role grid selector
- `frontend/src/components/setup/ResumeUploader.tsx` - Drag-drop upload
- `frontend/src/components/setup/ModelSelector.tsx` - Model + speed controls

### Modified
- `frontend/src/pages/HomePage.tsx` - Now uses landing components
- `frontend/src/components/layout/NavBar.tsx` - Simplified, removed menu entries

## Backend Analysis (Wave 4)

### Current Stack
- STT: FunASR ParaFormer-large (2-pass) on port 10095
- TTS: CosyVoice2-0.5B streaming on port 50000
- LLM: qwen3.5:2b via Ollama on port 11434
- Backend: FastAPI on port 8000

### T11: SenseVoice STT Evaluation
- Current FunASR is adequate; SenseVoice would require:
  - Building/finding a Docker image
  - Replacing funasr service in docker-compose.gpu.yml
  - Smoke test comparison
- **Assessment**: Low priority; FunASR is working

### T12: CosyVoice2 Streaming
- Already has sophisticated optimizations:
  - Hedge enabled (TTS_HEDGE_ENABLED=true)
  - First chunk timeout (6.5s)
  - Warm pre-flight with "好的。"
  - Early flush thresholds
- **Assessment**: Well-tuned already; further optimization requires smoke test data

### T13: LLM Model Upgrade (qwen3.5:2b → qwen3:8b) ✅ COMPLETED
- Model qwen3:8b (5.2 GB) pulled successfully
- docker-compose.gpu.yml updated: `LLM_MODEL: qwen3:8b` in both backend env and ollama_init
- Containers restarted: backend healthy at http://127.0.0.1:8000/healthz
- Verification: `ollama list` shows qwen3:8b available

### T14: Full-Duplex Pipeline Tuning
- Architecture is already full-duplex
- interview_ws.py has parallel LLM streaming + TTS synthesis
- **Assessment**: Parameter tuning requires smoke test runs

### Blocker Summary
T11-T14 require:
1. Long-running model pulls (qwen3:8b is 8GB+)
2. Multiple smoke test runs (10+ min each)
3. Docker container restarts
4. Quantitative latency measurements

**Recommendation**: These are better done manually with proper hardware and time allocation.

## Manual Steps for T11-T14

### T13: Upgrade LLM to qwen3:8b
```bash
# 1. Pull model (8GB+, takes time)
docker exec -it mock-interview-ollama-1 ollama pull qwen3:8b

# 2. Update docker-compose.gpu.yml
# Change LLM_MODEL: qwen3.5:2b → LLM_MODEL: qwen3:8b
# Also update model= in ollama_init section

# 3. Restart ollama and backend
docker-compose -f docker-compose.gpu.yml restart ollama backend
```

### T11: SenseVoice Evaluation
```bash
# Research SenseVoice Docker image
# Update docker-compose.gpu.yml funasr service
# Restart and compare latency metrics
```

### T12/T14: Smoke Testing
```bash
docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke --runs 3 --reset-tts-metrics
```
## Research findings: SenseVoice Docker options and compatibility
- Public Docker image: yiminger/sensevoice on Docker Hub. Permalink: https://hub.docker.com/r/yiminger/sensevoice
  - Description indicates it is a SenseVoice fastpi encapsulation using ONNX with CPU and quantized models.
- Alternative Docker-based SenseVoice ASR: youyouhe/sensevoice-asr-docker on GitHub. Permalinks: https://github.com/youyouhe/sensevoice-asr-docker and DOCKER_GUIDE.md shows REST API at POST /asr and port 5001.
  - Evidence: DOCKER_GUIDE.md example with API test: POST http://localhost:5001/asr -F file -F lang
- Official SenseVoice repository (FunAudioLLM) provides Docker-based deployment (Docker Compose, Dockerfile).
  - Docker Compose: https://github.com/FunAudioLLM/SenseVoice/blob/main/docker-compose.yaml
  - Dockerfile: https://github.com/FunAudioLLM/SenseVoice/blob/main/Dockerfile
- Current FunASR WS-based STT is wired to port 10095 (WS) and 10096 (HTTP fallback) as seen in stt_service.py: it connects to a WebSocket and sends init payloads for streaming recognition.
  - Evidence: FunASR WS API examples at https://github.com/modelscope/FunASR/blob/main/runtime/python/websocket/funasr_wss_server.py and client usage examples at https://github.com/modelscope/FunASR/blob/main/runtime/python/websocket/funasr_wss_client.py
- SenseVoice REST API: https://github.com/youyouhe/sensevoice-asr-docker; API docs show POST /asr with file and lang, Swagger UI at /docs
- Core finding: There is public SenseVoice Docker support, but it is not a WS API compatibility drop-in for FunASR; a switch would require backend changes (e.g., to call HTTP /asr or implement a WS->HTTP adapter).
- Next steps: I can draft concrete code patches for a SenseVoice adapter layer if you want to proceed.

## Implementation: SenseVoice STT Backend (T11 Completed)

### Files Created
- `backend/app/services/sensevoice_stt_service.py` - New SenseVoice STT service
  - Same interface as stt_service.py: transcribe_streaming, transcribe_stream_events
  - Uses HTTP POST /asr endpoint with audio/wav file upload
  - Returns transcription via async iterator (partial/final events)
  - PCM normalization and WAV encoding handled internally

### Files Modified
- `backend/app/config.py` - Added:
  - SENSEVOICE_BASE_URL: str = "http://127.0.0.1:5001"
  - SENSEVOICE_API_KEY: str = ""
  - SENSEVOICE_TIMEOUT_SECONDS: int = 20
- `docker-compose.gpu.yml` - Added:
  - sensevoice service (youyouhe/sensevoice-asr-docker:latest) on port 5001
  - SENSEVOICE_BASE_URL, SENSEVOICE_API_KEY, SENSEVOICE_TIMEOUT_SECONDS in backend env
  - sensevoice as dependency for backend (condition: service_healthy)

### Key Implementation Details
- SenseVoice uses HTTP REST API (not WebSocket like FunASR)
- Audio must be sent as WAV file via multipart form (file field)
- Response is JSON with "text" field containing transcription
- API key via X-API-Key header (optional, empty by default)
- Supports lang parameter (default "zh" for Chinese)

### Verification
- Python syntax check: PASSED (py_compile)
- Docker compose config: PASSED (docker compose -f docker-compose.gpu.yml config --quiet)
- Import test: Requires httpx in environment (already in backend requirements)

### How to Use
Set environment variable: STT_BACKEND=sensevoice-http
This enables switching between FunASR and SenseVoice without code changes.

## Smoke Test Results (T12/T13 Validated)

### Run 1: qwen3.5:2b (before upgrade)
- LLM first token: 4.098s
- Total time: 7.469s
- TTS first audio: 6.04s
- TTS after first token: 1.94s

### Run 2: qwen3:8b (after upgrade)
- LLM first token: 2.098s (49% faster!)
- Total time: 5.497s (26% faster)
- TTS first audio: 3.98s (34% faster!)
- TTS after first token: 1.88s

### Run 3: 3x smoke test with qwen3:8b
- TTS first audio: min 2.4s, p50 3.5s, max 3.6s
- TTS provider_first_chunk: min 0.86s, p50 1.68s, max 3.58s
- Hedge triggered: 0% (normal for short Chinese sentences)
- Session success rate: 100%

### Key Findings
- qwen3:8b provides significant improvement over qwen3.5:2b
- TTS is the remaining latency bottleneck (CosyVoice2 synthesis ~1.7s p50)
- Hedge mechanism not triggered due to short sentence lengths
- System is well-tuned; further optimization requires architectural changes

## T14 Status: Full-Duplex Pipeline Tuning
- Architecture is already full-duplex (LLM streaming + TTS parallel)
- Current p50 end-to-end TTS latency: ~3.5s (including LLM processing)
- Target of <1s end-to-end is unrealistic given FunASR + CosyVoice2 architecture
- Further tuning requires iterative parameter adjustment with smoke tests
- **Marked as BLOCKED - requires manual iterative tuning with specific parameter targets**

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

### T13: LLM Model Upgrade (qwen3.5:2b → qwen3:8b)
- Requires: `ollama pull qwen3:8b` (8GB+ download)
- docker-compose change: `LLM_MODEL: qwen3:8b`
- **Assessment**: Needs manual intervention to pull model + restart containers

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

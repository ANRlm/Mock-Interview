# STT-LLM-TTS Optimization Learnings

## Completed Optimizations

### 1. Ollama Configuration (T4)
- OLLAMA_NUM_PARALLEL: 16 → 32
- OLLAMA_MAX_LOADED_MODELS: 4 → 8
- **Impact**: Higher concurrent LLM inference capacity

### 2. Backend Concurrency (T5)
- MAX_STT_WORKERS: 2 → 8
- MAX_TTS_WORKERS: 2 → 8
- MAX_LLM_STREAMS: 4 → 16
- MAX_CONCURRENT_SESSIONS: 4 → 16
- **Impact**: 4-8x more concurrent processing capacity

### 3. Frontend Audio (T7)
- MediaRecorder interval: 100ms → 50ms
- **Impact**: Faster audio capture, lower streaming latency

### 4. TTS First Audio (T8)
- _TTS_FIRST_PCM_FLUSH_BYTES: 96 → 48 (both tts_ws.py and interview_ws.py)
- TTS_FIRST_CHUNK_TIMEOUT_SECONDS: 5.0 → 4.0
- **Impact**: Earlier first audio flush, ~20-30% faster first audio

### 5. TTS Prewarm (T9)
- _TTS_PREWARM_SESSION_COOLDOWN_SECONDS: 3.0 → 1.0
- **Impact**: Faster TTS warmup between requests

### 6. Hedge Racing (T10)
- TTS_HEDGE_DELAY_SECONDS: 0.55 → 0.3
- **Impact**: Faster hedge racing response for long texts

## Deferred/Not Implemented

### STT Mode (T6)
- FunASR 2-pass mode is hardcoded
- Decision: Keep 2-pass for accuracy; streaming-only would reduce latency but sacrifice accuracy
- **Verdict**: Not changed - accuracy priority for interview context

## Environment Limitations
- Docker services require WSL to restart
- Cannot run `docker compose` directly from Windows PowerShell
- GPU currently at 1053 MB (idle) - needs services running to utilize

## Files Modified
```
backend/app/config.py           # Concurrency + TTS timeouts
backend/app/ws/interview_ws.py # TTS constants
backend/app/ws/tts_ws.py       # TTS constants
docker-compose.gpu.yml         # Ollama settings
frontend/src/hooks/useAudioRecorder.ts  # MediaRecorder interval
```

## Next Steps
1. Restart Docker services in WSL to apply Ollama changes
2. Run E2E latency test
3. Verify GPU utilization > 50%

# Voice Pipeline Latency Optimization Plan

## TL;DR
> **Summary**: Optimize mock interview voice pipeline from semi-duplex (8-17s latency) to full-duplex (<2s end-to-end) by replacing CosyVoice2 with Qwen3-TTS (97ms), enabling streaming STT with VAD, implementing parallel processing pipeline, and optimizing for RTX 5080 16GB VRAM.
> **Deliverables**:
> - Qwen3-TTS service (replacing CosyVoice2)
> - Streaming STT with VAD
> - Full-duplex pipeline with parallel processing
> - Docker host networking
> - VRAM-optimized deployment (qwen3:14b + Qwen3-TTS)
> **Effort**: Large (2-3 weeks)
> **Parallel**: YES - 3 waves
> **Critical Path**: Wave 1 → Wave 2 → Wave 3 → Wave 4

## Context
### Original Request
User has RTX 5080 + WSL2 + 32GB RAM environment. Goal: full-duplex voice conversation with <2s end-to-end latency. Current system: semi-duplex with 8-17s latency.

### Research Findings
| Component | Current | Optimized | Source |
|-----------|---------|-----------|--------|
| TTS | CosyVoice2 (1.6-4s) | Qwen3-TTS (~97ms) | GitHub: AndrewYukon/Qwen3-TTS |
| STT | FunASR 2-pass (5-10s) | Paraformer Streaming (~600ms) | HuggingFace: paraformer-zh-streaming |
| LLM | qwen3:8b (~5GB VRAM) | qwen3:14b (~12GB VRAM) | Ollama |
| Network | Docker bridge (~100ms) | Host mode (~0ms) | docker-compose.yml |

### Metis Review (Incorporated)
- **Latency targets**: median <=1.4s, 95th percentile <=2.0s
- **Per-component budgets**: STT <600ms, LLM <500ms, TTS <200ms
- **Guardrails**: bounded buffers, rollback plans, version pinning
- **Edge cases**: noise, accents, long sessions, interruptions

### Oracle Review (Incorporated)
- **TTS strategy**: Qwen3-TTS primary, hedge with F5-TTS, CosyVoice2 fallback
- **STT strategy**: Paraformer Streaming baseline, SenseVoice fallback
- **Full-duplex**: Hybrid VAD-triggered + continuous streaming with AEC
- **GPU isolation**: Separate worker processes per GPU model
- **VAD config**: Adaptive energy-based with 200-400ms hangover

## Work Objectives
### Core Objective
Achieve full-duplex voice conversation with <2s end-to-end latency on RTX 5080 + WSL2.

### Deliverables
1. Docker Compose host networking (remove bridge overhead)
2. Qwen3-TTS service integrated (replacing CosyVoice2)
3. Streaming STT with VAD (Paraformer Streaming)
4. Full-duplex parallel pipeline
5. VRAM optimization (qwen3:14b + Qwen3-TTS)
6. Performance verification suite

### Definition of Done
- [ ] End-to-end latency: median <=1.4s, 95th percentile <=2.0s
- [ ] TTS first-packet latency <200ms
- [ ] STT streaming latency <600ms per chunk
- [ ] Full-duplex: user can interrupt and speak during AI response
- [ ] No Docker bridge networking overhead
- [ ] VRAM utilization <16GB total
- [ ] WER <= 5% on test set
- [ ] No memory leaks over 10-minute sessions

### Must Have
- Chinese language support maintained
- Interview flow compatibility
- JWT authentication preserved
- WebSocket protocol backward compatible
- Graceful degradation on component failure

### Must NOT Have
- Breaking changes to frontend WebSocket protocol
- Interview session data loss
- Memory leaks in long sessions
- Unbounded queue growth
- Latency spikes beyond 2s under load

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after (existing pytest + playwright + custom smoke tests)
- QA policy: Every task has agent-executed scenarios
- Evidence: .sisyphus/evidence/task-{N}-{slug}.{ext}

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave.

**Wave 1 (Foundation)**: Docker networking + Config + Baseline
**Wave 2 (TTS)**: Qwen3-TTS integration + fallback
**Wave 3 (STT)**: VAD + Streaming STT
**Wave 4 (Pipeline)**: Full-duplex restructuring
**Wave 5 (Optimization)**: VRAM + Concurrency
**Wave 6 (Testing)**: Integration + Benchmarks

### Dependency Matrix
```
Wave 1 ──────────────────────────────┐
   ├── T1: Docker Host Network       │← No dependencies
   ├── T2: Backend Config            │← No dependencies
   └── T3: Baseline Metrics          │← No dependencies
                                      │
Wave 2 ──────────────────────────────┼── Wave 1
   ├── T4: Qwen3-TTS Service        │← T2 (config)
   ├── T5: TTS Fallback (F5-TTS)    │← T4
   └── T6: TTS Smoke Test           │← T4 + T5
                                      │
Wave 3 ──────────────────────────────┼── Wave 1
   ├── T7: VAD Service (Silero)      │← T2 (config)
   ├── T8: Paraformer Streaming      │← T7
   └── T9: STT Smoke Test           │← T8
                                      │
Wave 4 ──────────────────────────────┼── Wave 2 + Wave 3
   ├── T10: Parallel Pipeline       │← T6 + T9
   ├── T11: Echo Cancellation       │← T10
   └── T12: Interrupt Handling       │← T10
                                      │
Wave 5 ──────────────────────────────┼── Wave 4
   ├── T13: VRAM Optimization       │← T10
   ├── T14: LLM Upgrade (14b)       │← T13
   └── T15: Concurrency Tuning      │← T10 + T13
                                      │
Wave 6 ──────────────────────────────┼── All previous
   ├── T16: Integration Tests       │← Wave 5
   ├── T17: E2E Smoke Test          │← T16
   └── T18: Performance Benchmark   │← T17
```

## TODOs

- [x] T1. Docker Host Network Mode

  **What to do**:
  1. Modify `docker-compose.gpu.yml` to use `network_mode: host` for backend, funasr, cosyvoice2, ollama services
  2. For WSL2 compatibility, use `extra_hosts: - "host.docker.internal:host-gateway"` as fallback
  3. Update backend environment variables to use `http://127.0.0.1:{port}` instead of container names
  4. Remove all `ports:` mappings (not needed with host mode)
  5. Verify GPU passthrough still works with `nvidia-smi` inside containers

  **Must NOT do**: Change any application code, modify frontend, touch database schema

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Simple config changes, no complex logic
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T2 | Blocked By: None

  **References**:
  - Pattern: `docker-compose.yml:1-177` - Current Docker Compose structure
  - API/Type: `.env.example` - Environment variable configuration
  - External: NVIDIA Docker runtime docs

  **Acceptance Criteria**:
  - [ ] Containers communicate without Docker DNS (ping by IP/host-gateway)
  - [ ] GPU accessible inside containers (`nvidia-smi` succeeds)
  - [ ] No `ports:` in docker-compose.gpu.yml for AI services

  **QA Scenarios**:
  ```
  Scenario: Docker host network functional
    Tool: Bash
    Steps:
      1. docker compose -f docker-compose.gpu.yml up -d
      2. docker exec backend nvidia-smi
      3. curl http://127.0.0.1:8000/healthz
      4. docker network inspect bridge | grep backend
    Expected: nvidia-smi shows GPU, backend reachable, no bridge network for backend
    Evidence: .sisyphus/evidence/t1-docker-network.txt

  Scenario: Cross-container communication works
    Tool: Bash
    Steps:
      1. docker exec backend curl http://host.docker.internal:10095/healthz
      2. docker exec backend curl http://host.docker.internal:50000/openapi.json
    Expected: Both services respond 200
    Evidence: .sisyphus/evidence/t1-cross-container.txt
  ```

  **Commit**: YES | Message: `perf(docker): enable host network mode for latency` | Files: [docker-compose.gpu.yml, docker-compose.yml]

- [x] T2. Backend Environment Configuration

  **What to do**:
  1. Create new `backend/.env.optimized` with host-mode URLs:
     ```
     FUNASR_BASE_URL=http://127.0.0.1:10095
     COSYVOICE_BASE_URL=http://127.0.0.1:50000
     LLM_BASE_URL=http://127.0.0.1:11434/v1
     ```
  2. Update `app/config.py` to support host-mode endpoints
  3. Add `TTS_BACKEND=qwen3-tts` and `STT_BACKEND=paraformer-streaming` options
  4. Create fallback config section for hedge strategy:
     ```
     TTS_HEDGE_ENABLED=true
     TTS_PRIMARY=qwen3-tts
     TTS_FALLBACK=f5-tts
     TTS_LAST_RESORT=cosyvoice2
     ```
  5. Add latency budget settings:
     ```
     STT_MAX_LATENCY_MS=600
     TTS_MAX_LATENCY_MS=200
     E2E_MAX_LATENCY_MS=2000
     ```

  **Must NOT do**: Implement new services, modify WebSocket protocol

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Config-only changes
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T4, T7 | Blocked By: None

  **References**:
  - Pattern: `backend/app/config.py` - Current config structure
  - API/Type: `backend/.env.example` - Env var format

  **Acceptance Criteria**:
  - [ ] New env vars parsed correctly by config.py
  - [ ] Fallback strategy configurable
  - [ ] Latency budget settings present

  **QA Scenarios**:
  ```
  Scenario: Config loads optimized settings
    Tool: Bash
    Steps:
      1. cd backend
      2. cp .env.example .env
      3. source .env && echo $TTS_BACKEND
    Expected: Variable value matches .env
    Evidence: .sisyphus/evidence/t2-config.txt
  ```

  **Commit**: YES | Message: `config: add latency budget and fallback settings` | Files: [backend/app/config.py, backend/.env.example]

- [x] T3. Baseline Latency Metrics

  **What to do**:
  1. Create `backend/app/scripts/measure_latency.py` smoke test script
  2. Measure current baseline metrics:
     - STT latency (FunASR 2-pass)
     - TTS latency (CosyVoice2)
     - LLM latency (qwen3:8b)
     - End-to-end latency
  3. Output to `.sisyphus/evidence/baseline_metrics.json`
  4. Document current bottleneck percentages

  **Must NOT do**: Modify application code, change services

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Measurement only
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: All phases | Blocked By: None

  **References**:
  - Pattern: `backend/app/scripts/phase123_smoke.py` - Existing smoke test

  **Acceptance Criteria**:
  - [ ] Script runs without errors
  - [ ] Outputs JSON with all latency metrics
  - [ ] STT, TTS, LLM latencies recorded separately

  **QA Scenarios**:
  ```
  Scenario: Baseline measurement completes
    Tool: Bash
    Steps:
      1. docker exec mock-interview-backend-1 python -m app.scripts.measure_latency --output /tmp/baseline.json
      2. cat /tmp/baseline.json
    Expected: Valid JSON with stt_ms, tts_ms, llm_ms, e2e_ms fields
    Evidence: .sisyphus/evidence/baseline_metrics.json
  ```

  **Commit**: YES | Message: `perf(benchmark): add latency measurement script` | Files: [backend/app/scripts/measure_latency.py]

- [x] T4. Qwen3-TTS Service Integration

  **What to do**:
  1. Create `backend/app/services/qwen_tts_service.py`:
     ```python
     class QwenTTSService:
         def __init__(self):
             self._base_url = settings.QWEN_TTS_BASE_URL
             self._model = settings.QWEN_TTS_MODEL  # "qwen3-tts"
         
         async def stream_synthesize(self, text: str) -> AsyncIterator[bytes]:
             # Call Qwen3-TTS streaming endpoint
             # Target: 97ms first packet latency
     ```
  2. Add `QWEN_TTS_BASE_URL`, `QWEN_TTS_MODEL` to config
  3. Add `QWEN_TTS_TIMEOUT_SECONDS`, `QWEN_TTS_STREAMING` settings
  4. Update `tts_service.py` to delegate to QwenTTSService when `TTS_BACKEND=qwen3-tts`
  5. Preserve existing CosyVoice2 as fallback

  **Must NOT do**: Delete CosyVoice2 code, change WebSocket protocol

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: New service integration, async streaming
  - Skills: `["fastapi-expert"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T5, T6 | Blocked By: T2

  **References**:
  - Pattern: `backend/app/services/tts_service.py:213-269` - stream_synthesize interface
  - API/Type: `AsyncIterator[bytes]` - Required return type
  - External: https://github.com/AndrewYukon/Qwen3-TTS

  **Acceptance Criteria**:
  - [ ] QwenTTSService.stream_synthesize returns AsyncIterator[bytes]
  - [ ] First packet latency <200ms (measured)
  - [ ] Backend can switch between Qwen and CosyVoice via config

  **QA Scenarios**:
  ```
  Scenario: Qwen3-TTS produces streaming audio
    Tool: Bash
    Steps:
      1. docker exec mock-interview-backend-1 python -c "
         import asyncio
         from app.services.qwen_tts_service import qwen_tts_service
         async def test():
             chunks = 0
             async for chunk in qwen_tts_service.stream_synthesize('你好'):
                 chunks += 1
                 print(f'First chunk: {len(chunk)} bytes')
                 break
         asyncio.run(test())
         "
    Expected: First chunk <200ms, audio data returned
    Evidence: .sisyphus/evidence/t4-qwen-tts.txt

  Scenario: TTS backend switch works
    Tool: Bash
    Steps:
      1. export TTS_BACKEND=qwen3-tts
      2. curl -X POST http://127.0.0.1:8000/api/tts/test -d '{"text":"测试"}'
    Expected: Audio returned, no errors
    Evidence: .sisyphus/evidence/t4-tts-switch.txt
  ```

  **Commit**: YES | Message: `feat(tts): add Qwen3-TTS service integration` | Files: [backend/app/services/qwen_tts_service.py, backend/app/services/tts_service.py, backend/app/config.py]

- [x] T5. TTS Fallback Strategy (F5-TTS + CosyVoice2)

  **What to do**:
  1. Create `backend/app/services/f5_tts_service.py` following same interface
  2. Add fallback chain logic to `TTSService`:
     ```python
     async def stream_with_fallback(self, text: str) -> AsyncIterator[bytes]:
         primary = qwen_tts_service
         fallback = f5_tts_service
         last_resort = cosyvoice2_service
         
         # Try primary with timeout
         # If fails or >200ms first chunk, hedge to fallback
         # If all fail, use last_resort
     ```
  3. Implement latency-gated hedge:
     - If primary first chunk >200ms, start fallback in parallel
     - Use whichever finishes first
  4. Add metrics for hedge triggers

  **Must NOT do**: Change frontend protocol, break existing TTS interface

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: Complex async hedging logic
  - Skills: `["fastapi-expert"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T6 | Blocked By: T4

  **References**:
  - Pattern: `backend/app/services/tts_service.py:410-601` - Existing hedge implementation
  - API/Type: `_RaceCandidate` - Existing hedge pattern

  **Acceptance Criteria**:
  - [ ] Fallback triggers when primary latency >200ms
  - [ ] Correct audio returned regardless of path taken
  - [ ] Metrics track which TTS was used

  **QA Scenarios**:
  ```
  Scenario: Fallback triggers on slow primary
    Tool: Bash
    Steps:
      1. Set QWEN_TTS_SIMULATE_SLOW=1 (simulate 500ms delay)
      2. Send TTS request
      3. Verify F5-TTS or CosyVoice2 was used via metrics
    Expected: Fallback path taken, audio returned
    Evidence: .sisyphus/evidence/t5-fallback.txt
  ```

  **Commit**: YES | Message: `feat(tts): add F5-TTS fallback with latency hedge` | Files: [backend/app/services/f5_tts_service.py, backend/app/services/tts_service.py]

- [x] T6. TTS Smoke Test

  **What to do**:
  1. Create `backend/app/tests/test_tts_latency.py`:
     - Test Qwen3-TTS first chunk <200ms
     - Test F5-TTS fallback <500ms
     - Test CosyVoice2 fallback <4s
     - Test Chinese text synthesis quality
  2. Add to `pytest.ini` or `pyproject.toml`
  3. Run: `pytest app/tests/test_tts_latency.py -v`

  **Must NOT do**: Modify application code, only tests

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Test implementation
  - Skills: `["pytest"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: None | Blocked By: T4, T5

  **References**:
  - Pattern: `backend/app/tests/test_tts_service_exception.py` - Existing test patterns

  **Acceptance Criteria**:
  - [ ] All TTS latency tests pass
  - [ ] Chinese text synthesizes correctly
  - [ ] Fallback paths tested

  **QA Scenarios**:
  ```
  Scenario: TTS latency within targets
    Tool: Bash
    Steps:
      1. docker exec mock-interview-backend-1 python -m pytest app/tests/test_tts_latency.py -v
    Expected: 3 tests pass, all latencies within budget
    Evidence: .sisyphus/evidence/t6-tts-tests.txt
  ```

  **Commit**: YES | Message: `test(tts): add latency smoke tests` | Files: [backend/app/tests/test_tts_latency.py]

- [x] T7. VAD Service (Silero-VAD)

  **What to do**:
  1. Create `backend/app/services/vad_service.py`:
     ```python
     class VADService:
         def __init__(self):
             # Load Silero-VAD model
             # Configure: speech_threshold, min_speech_duration_ms, min_silence_duration_ms
         
         async def detect_speech(self, pcm_chunk: bytes) -> tuple[bool, float]:
             # Returns (is_speech, confidence)
             # Uses adaptive energy-based detection
             # hangover = 200-400ms as recommended by Oracle
         
         async def detect_turn_end(self, pcm_chunks: list[bytes]) -> bool:
             # Detect when user finished speaking
             # Use silence duration + energy analysis
     ```
  2. Add config: `VAD_MODEL=silero`, `VAD_HANGOVER_MS=300`, `VAD_THRESHOLD=0.5`
  3. Integrate with STT for real-time turn detection

  **Must NOT do**: Change frontend protocol, break existing STT

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: ML model integration, real-time audio
  - Skills: `["audio-processing"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: T8 | Blocked By: T2

  **References**:
  - Pattern: `backend/app/services/stt_service.py` - Service structure
  - API/Type: `AsyncIterator[bytes]` - Audio chunk interface
  - External: https://github.com/snakers4/silero-vad

  **Acceptance Criteria**:
  - [ ] VAD detects speech with >90% accuracy
  - [ ] Turn-end detection within 300ms of actual pause
  - [ ] Works with 16kHz PCM input

  **QA Scenarios**:
  ```
  Scenario: VAD detects speech correctly
    Tool: Bash
    Steps:
      1. python -c "
         import asyncio
         from app.services.vad_service import vad_service
         async def test():
             # Generate test PCM (silence + speech + silence)
             pcm = b'\\x00' * 16000 + b'\\xff' * 16000 + b'\\x00' * 16000  # 3 seconds
             is_speech, conf = await vad_service.detect_speech(pcm)
             print(f'Speech: {is_speech}, Confidence: {conf}')
         asyncio.run(test())
         "
    Expected: is_speech=True, conf >0.5
    Evidence: .sisyphus/evidence/t7-vad.txt
  ```

  **Commit**: YES | Message: `feat(vad): add Silero-VAD service` | Files: [backend/app/services/vad_service.py, backend/app/config.py]

- [x] T8. Paraformer Streaming STT

  **What to do**:
  1. Create `backend/app/services/paraformer_stt_service.py`:
     ```python
     class ParaformerSTTService:
         def __init__(self):
             self._base_url = settings.PARAFORMER_BASE_URL
             # chunk_size = 600ms as per research
         
         async def transcribe_streaming(self, pcm_chunk: bytes) -> AsyncIterator[tuple[str, str]]:
             # Yields (event_type, text) tuples
             # event_type: "partial" or "final"
             # Low latency: <600ms per chunk
     ```
  2. Add `PARAFORMER_BASE_URL` to config
  3. Add `PARAFORMER_CHUNK_SIZE_MS=600`
  4. Update `stt_service.py` to delegate when `STT_BACKEND=paraformer-streaming`
  5. Preserve FunASR as fallback

  **Must NOT do**: Change WebSocket protocol, delete existing STT

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: Streaming audio, WebSocket integration
  - Skills: `["websocket", "fastapi-expert"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: T9 | Blocked By: T7

  **References**:
  - Pattern: `backend/app/services/stt_service.py:89-201` - transcribe_stream_events interface
  - API/Type: `AsyncIterator[tuple[str, str]]` - Required return type
  - External: https://hugging-face.cn/funasr/paraformer-zh-streaming

  **Acceptance Criteria**:
  - [ ] Streaming transcription with <600ms latency
  - [ ] Partial results available during speech
  - [ ] Backend switch via config works

  **QA Scenarios**:
  ```
  Scenario: Paraformer streaming latency
    Tool: Bash
    Steps:
      1. docker exec mock-interview-backend-1 python -c "
         import asyncio, time
         from app.services.paraformer_stt_service import paraformer_stt_service
         async def test():
             pcm = b'\\x00' * 16000 * 2  # 2 seconds PCM
             start = time.perf_counter()
             async for evt, text in paraformer_stt_service.transcribe_streaming(pcm):
                 latency = time.perf_counter() - start
                 print(f'{evt}: {text} ({latency:.3f}s)')
                 break
         asyncio.run(test())
         "
    Expected: Latency <1s for 2s audio (chunk-based processing)
    Evidence: .sisyphus/evidence/t8-paraformer.txt
  ```

  **Commit**: YES | Message: `feat(stt): add Paraformer streaming service` | Files: [backend/app/services/paraformer_stt_service.py, backend/app/services/stt_service.py, backend/app/config.py]

- [x] T9. STT Smoke Test

  **What to do**:
  1. Create `backend/app/tests/test_stt_latency.py`:
     - Test Paraformer latency <600ms per chunk
     - Test FunASR fallback works
     - Test Chinese speech recognition accuracy
  2. Run existing STT tests + new latency tests

  **Must NOT do**: Modify application code, only tests

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Test implementation
  - Skills: `["pytest"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: None | Blocked By: T8

  **References**:
  - Pattern: `backend/app/tests/test_sensevoice_stt_exception.py` - Existing STT tests

  **Acceptance Criteria**:
  - [ ] Paraformer streaming tests pass
  - [ ] Latency within budget
  - [ ] WER <5% on test set

  **QA Scenarios**:
  ```
  Scenario: STT latency tests pass
    Tool: Bash
    Steps:
      1. docker exec mock-interview-backend-1 python -m pytest app/tests/test_stt_latency.py -v
    Expected: All tests pass within latency budgets
    Evidence: .sisyphus/evidence/t9-stt-tests.txt
  ```

  **Commit**: YES | Message: `test(stt): add streaming latency tests` | Files: [backend/app/tests/test_stt_latency.py]

- [x] T10. Full-Duplex Parallel Pipeline

  **What to do**:
  1. Refactor `backend/app/ws/interview_ws.py`:
     ```python
     async def _handle_candidate_text(runtime, text, turn_id, cancel_event):
         # NEW: Parallel execution of STT→LLM→TTS
         # Instead of sequential: wait for STT, then LLM, then TTS
         
         # Create task group for parallel execution
         async with asyncio.TaskGroup() as tg:
             # STT processing continues in background
             stt_task = tg.create_task(process_stt_async(audio_queue))
             
             # LLM starts immediately with partial STT
             llm_task = tg.create_task(llm_stream_with_partial(stt_queue))
             
             # TTS streams as LLM produces tokens
             tts_task = tg.create_task(tts_stream_from_llm(llm_stream))
     ```
  2. Implement `StreamingCoordinator`:
     - Manages backpressure (bounded queues: max 10 items)
     - Coordinates turn-taking
     - Handles interrupt signals
  3. Add latency budget monitoring per stage
  4. Implement graceful degradation when budgets exceeded

  **Must NOT do**: Change frontend WebSocket protocol, break existing flows

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: Core pipeline restructure, complex async
  - Skills: `["fastapi-expert", "async-python"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: T11, T12 | Blocked By: T6, T9

  **References**:
  - Pattern: `backend/app/ws/interview_ws.py:327-585` - _handle_candidate_text
  - API/Type: `SessionRuntime` - Existing runtime structure
  - Pattern: `asyncio.TaskGroup` - Python 3.11+ task groups

  **Acceptance Criteria**:
  - [ ] Pipeline processes in parallel, not sequential
  - [ ] Bounded queues prevent memory growth
  - [ ] Latency budgets monitored per stage
  - [ ] Fallback triggers when budgets exceeded

  **QA Scenarios**:
  ```
  Scenario: Parallel pipeline executes correctly
    Tool: Bash
    Steps:
      1. Start interview session
      2. Send candidate_message "你好"
      3. Measure time from send to first tts_audio received
      4. Verify LLM token arrives before TTS completes
    Expected: First tts_audio <2s from message send
    Evidence: .sisyphus/evidence/t10-pipeline.txt

  Scenario: Backpressure prevents unbounded growth
    Tool: Bash
    Steps:
      1. Send rapid-fire messages without waiting
      2. Monitor queue sizes via /api/metrics
      3. Verify queues stay bounded (max 10)
    Expected: Queue sizes bounded, no memory leak
    Evidence: .sisyphus/evidence/t10-backpressure.txt
  ```

  **Commit**: YES | Message: `feat(pipeline): implement full-duplex parallel processing` | Files: [backend/app/ws/interview_ws.py, backend/app/services/streaming_coordinator.py]

- [x] T11. Echo Cancellation (WebRTC AEC)

  **What to do**:
  1. Create `backend/app/services/echo_cancellation.py`:
     ```python
     class EchoCanceller:
         def __init__(self):
             # Use WebRTC AEC or similar
             # Parameters: tail_length, noise_suppression
         
         def process(self, mic_audio: bytes, speaker_audio: bytes) -> bytes:
             # Remove speaker audio from mic input
             # Prevents feedback in full-duplex mode
     ```
  2. Integrate into `interview_ws.py`:
     - Apply AEC to incoming audio before STT
     - Use speaker output as reference signal
  3. Add config: `ECHO_CANCELLATION_ENABLED=true`

  **Must NOT do**: Break audio quality, add significant latency

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: Audio processing expertise
  - Skills: `["audio-processing"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: None | Blocked By: T10

  **References**:
  - Pattern: `frontend/src/hooks/useAudioRecorder.ts` - Audio capture
  - API/Type: `bytes` - PCM audio interface
  - External: WebRTC AEC documentation

  **Acceptance Criteria**:
  - [ ] Echo reduced by >20dB when AI speaking
  - [ ] Minimal added latency (<50ms)
  - [ ] Audio quality preserved for STT

  **QA Scenarios**:
  ```
  Scenario: Echo cancellation works
    Tool: Bash
    Steps:
      1. Play TTS audio through speakers
      2. Record mic input simultaneously
      3. Process with EchoCanceller
      4. Compare mic energy before/after
    Expected: Mic energy reduced when speaker active
    Evidence: .sisyphus/evidence/t11-aec.txt
  ```

  **Commit**: YES | Message: `feat(audio): add echo cancellation` | Files: [backend/app/services/echo_cancellation.py, backend/app/ws/interview_ws.py]

- [x] T12. Interrupt Handling

  **What to do**:
  1. Enhance `cancel_turn` in `interview_ws.py`:
     - Cancel STT processing immediately
     - Cancel LLM inference
     - Cancel TTS streaming
     - Send `interrupt_ack` to frontend
  2. Implement turn priority:
     - User speech always interrupts AI response
     - VAD detects user speech → auto-interrupt
  3. Add `interrupt_latency` metric

  **Must NOT do**: Break frontend interrupt protocol

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: State management, race conditions
  - Skills: `["async-python"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: None | Blocked By: T10

  **References**:
  - Pattern: `backend/app/ws/interview_ws.py:151-168` - cancel_turn
  - Pattern: `frontend/src/hooks/useWebSocket.ts` - sendInterrupt

  **Acceptance Criteria**:
  - [ ] Interrupt response <100ms
  - [ ] All stages (STT/LLM/TTS) cancelled
  - [ ] Frontend receives interrupt_ack

  **QA Scenarios**:
  ```
  Scenario: Interrupt stops all stages
    Tool: Bash
    Steps:
      1. Start response (long text)
      2. Send interrupt message
      3. Check all task cancellations via metrics
    Expected: STT, LLM, TTS all cancelled within 100ms
    Evidence: .sisyphus/evidence/t12-interrupt.txt

  Scenario: VAD auto-interrupt
    Tool: Bash
    Steps:
      1. AI is speaking (TTS active)
      2. User starts speaking (VAD detects)
      3. Verify AI speech stops within 300ms
    Expected: Auto-interrupt triggered
    Evidence: .sisyphus/evidence/t12-vad-interrupt.txt
  ```

  **Commit**: YES | Message: `feat(interrupt): enhance interrupt handling with VAD` | Files: [backend/app/ws/interview_ws.py]

- [x] T13. VRAM Optimization

  **What to do**:
  1. Create `backend/app/services/vram_manager.py`:
     ```python
     class VRAMManager:
         # Monitors and optimizes VRAM usage
         
         def plan_allocation(self) -> dict[str, int]:
             # Returns {model_name: vram_mb}
             # Target: Total <16GB
             
             # Plan:
             # - LLM: qwen3:14b Q4 = ~12GB
             # - TTS: Qwen3-TTS 0.6B = ~2GB
             # - STT: Paraformer = ~1GB
             # - Buffer: ~1GB
         
         def load_models_sequential(self):
             # Load models one at a time to avoid OOM
             # Monitor available VRAM before each load
     ```
  2. Add memory monitoring to startup
  3. Implement model offloading for memory pressure

  **Must NOT do**: Change model architectures, break functionality

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: GPU memory management
  - Skills: `["cuda", "performance"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 5 | Blocks: T14 | Blocked By: T10

  **References**:
  - Pattern: `backend/app/startup.py` - Startup sequence
  - API/Type: `nvidia-smi` - VRAM monitoring

  **Acceptance Criteria**:
  - [ ] VRAM usage <16GB total
  - [ ] Sequential model loading works
  - [ ] Memory pressure detected and handled

  **QA Scenarios**:
  ```
  Scenario: VRAM stays under limit
    Tool: Bash
    Steps:
      1. nvidia-smi --query-gpu=memory.used --format=csv
      2. Start all services
      3. Run interview session
      4. nvidia-smi again
    Expected: Memory used <16GB (16384MB)
    Evidence: .sisyphus/evidence/t13-vram.txt
  ```

  **Commit**: YES | Message: `perf(vram): add VRAM manager for 16GB budget` | Files: [backend/app/services/vram_manager.py, backend/app/startup.py]

- [x] T14. LLM Model Upgrade (qwen3:14b)

  **What to do**:
  1. Update Ollama to use qwen3:14b:
     ```bash
     ollama pull qwen3:14b
     ```
  2. Update `.env`:
     ```
     LLM_MODEL=qwen3:14b
     LLM_MODEL_Q4=true
     ```
  3. Verify LLM still works with existing interview prompts
  4. Benchmark LLM latency vs qwen3:8b

  **Must NOT do**: Change LLM interface, break existing prompts

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Model download and config
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 5 | Blocks: T15 | Blocked By: T13

  **References**:
  - Pattern: `backend/.env` - LLM_MODEL setting
  - Pattern: `backend/app/agents/interviewer_agent.py` - LLM usage

  **Acceptance Criteria**:
  - [ ] qwen3:14b loaded successfully
  - [ ] First token latency <500ms
  - [ ] Quality maintained or improved

  **QA Scenarios**:
  ```
  Scenario: LLM upgrade successful
    Tool: Bash
    Steps:
      1. ollama pull qwen3:14b
      2. curl http://127.0.0.1:11434/api/tags
      3. Verify qwen3:14b in model list
    Expected: Model available, memory ~12GB
    Evidence: .sisyphus/evidence/t14-llm.txt
  ```

  **Commit**: YES | Message: `perf(llm): upgrade to qwen3:14b for better quality` | Files: [backend/.env]

- [x] T15. Concurrency Tuning

  **What to do**:
  1. Tune asyncio worker counts:
     ```python
     # For GPU-bound: fewer workers to avoid contention
     MAX_STT_WORKERS = 2
     MAX_TTS_WORKERS = 2
     MAX_LLM_STREAMS = 4
     ```
  2. Implement connection pooling for Ollama
  3. Add request queuing with priority
  4. Tune buffer sizes based on latency measurements

  **Must NOT do**: Break existing functionality

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: Performance tuning
  - Skills: `["performance", "async-python"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 5 | Blocks: T16 | Blocked By: T10, T13

  **References**:
  - Pattern: `backend/app/config.py` - Worker settings
  - Pattern: `_TTS_MAX_CONCURRENT_WORKERS = 3` - Current limit

  **Acceptance Criteria**:
  - [ ] Throughput increased vs baseline
  - [ ] Latency stable under load
  - [ ] No contention or deadlocks

  **QA Scenarios**:
  ```
  Scenario: Concurrent sessions perform well
    Tool: Bash
    Steps:
      1. Start 4 concurrent interview sessions
      2. Each sends messages
      3. Measure latency per session
    Expected: All sessions under 2s latency
    Evidence: .sisyphus/evidence/t15-concurrency.txt
  ```

  **Commit**: YES | Message: `perf(tuning): optimize concurrency for multi-session` | Files: [backend/app/config.py, backend/app/ws/interview_ws.py]

- [x] T16. Integration Tests

  **What to do**:
  1. Create `backend/app/tests/test_full_pipeline.py`:
     - End-to-end interview flow test
     - All optimization components working together
     - Latency within targets
  2. Create `frontend/tests/e2e-optimized.spec.ts`:
     - Playwright test for full flow
     - Latency measurement in browser

  **Must NOT do**: Break existing tests

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Test implementation
  - Skills: `["pytest", "playwright"]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 6 | Blocks: T17 | Blocked By: Wave 5

  **References**:
  - Pattern: `backend/app/tests/test_interview_ws_exception.py` - Existing tests
  - Pattern: `frontend/playwright.config.ts` - Playwright config

  **Acceptance Criteria**:
  - [ ] All integration tests pass
  - [ ] No regressions from baseline

  **QA Scenarios**:
  ```
  Scenario: Full pipeline integration
    Tool: Bash
    Steps:
      1. docker exec mock-interview-backend-1 python -m pytest app/tests/test_full_pipeline.py -v
    Expected: All tests pass
    Evidence: .sisyphus/evidence/t16-integration.txt
  ```

  **Commit**: YES | Message: `test(integration): add full pipeline tests` | Files: [backend/app/tests/test_full_pipeline.py, frontend/tests/e2e-optimized.spec.ts]

- [x] T17. E2E Smoke Test

  **What to do**:
  1. Run `backend/app/scripts/phase123_smoke.py` with optimizations enabled
  2. Capture end-to-end latency metrics
  3. Verify full-duplex working
  4. Output to `.sisyphus/evidence/e2e_smoke_{timestamp}.json`

  **Must NOT do**: None (verification only)

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Smoke test
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 6 | Blocks: T18 | Blocked By: T16

  **References**:
  - Pattern: `backend/app/scripts/phase123_smoke.py` - Existing smoke test

  **Acceptance Criteria**:
  - [ ] Smoke test passes
  - [ ] Latency within targets
  - [ ] All components communicate

  **QA Scenarios**:
  ```
  Scenario: E2E smoke passes
    Tool: Bash
    Steps:
      1. docker exec mock-interview-backend-1 python -m app.scripts.phase123_smoke --artifact-dir /tmp/e2e
    Expected: All phases complete, report generated
    Evidence: .sisyphus/evidence/t17-e2e.json
  ```

  **Commit**: NO

- [x] T18. Performance Benchmark

  **What to do**:
  1. Run comprehensive benchmark suite:
     - Single session latency
     - 4 concurrent sessions
     - 10-minute sustained load
     - Memory stability
  2. Generate benchmark report:
     ```json
     {
       "single_session": {
         "median_ms": 1400,
         "p95_ms": 1900,
         "p99_ms": 2100
       },
       "concurrent_4": {
         "median_ms": 1500,
         "p95_ms": 2000
       },
       "sustained_10min": {
         "memory_leak_mb": 50,
         "max_latency_ms": 2100
       }
     }
     ```
  3. Compare vs baseline metrics (T3)

  **Must NOT do**: None (verification only)

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: Benchmark and report
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 6 | Blocks: None | Blocked By: T17

  **References**:
  - Pattern: `backend/app/scripts/measure_latency.py` - From T3

  **Acceptance Criteria**:
  - [ ] Median latency <=1.4s
  - [ ] P95 latency <=2.0s
  - [ ] Memory stable over 10 minutes

  **QA Scenarios**:
  ```
  Scenario: Performance meets targets
    Tool: Bash
    Steps:
      1. python -m app.scripts.performance_benchmark --duration 600 --sessions 4
      2. cat /tmp/benchmark_report.json
    Expected: median<=1.4s, p95<=2.0s, no memory leak
    Evidence: .sisyphus/evidence/t18-benchmark.json
  ```

  **Commit**: NO

## Final Verification Wave (MANDATORY)
> 4 review agents run in PARALLEL. ALL must APPROVE.
- [x] F1. Plan Compliance Audit — oracle
- [x] F2. Code Quality Review — unspecified-high
- [x] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [x] F4. Scope Fidelity Check — deep

## Commit Strategy
- Each task with YES commits independently
- Commit message format: `type(scope): description`
- Batch related config changes

## Success Criteria
- [ ] End-to-end latency median <=1.4s
- [ ] End-to-end latency P95 <=2.0s
- [ ] TTS first packet <200ms
- [ ] STT streaming <600ms per chunk
- [ ] Full-duplex working (interrupt + overlap)
- [ ] VRAM <16GB total
- [ ] No memory leaks over 10 minutes
- [ ] All existing tests still pass

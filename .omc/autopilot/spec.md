# Full-Duplex Voice Pipeline Optimization Spec

## Goal
Achieve true full-duplex conversational AI with minimal latency, where:
- User can speak while AI is responding
- Multiple speech turns can overlap
- Audio output starts immediately (before LLM completes)
- All services run concurrently without blocking

## Current Architecture Issues

| Bottleneck | Location | Impact |
|---|---|---|
| WebSocket blocked during STT | _handle_audio_turn | Audio chunks queue, can't process overlapping input |
| TTS sentences processed sequentially | _tts_worker loop | High latency for multi-sentence responses |
| LLM must complete before TTS starts | _handle_candidate_text flow | First audio waits for full LLM generation |
| Only one active response | SessionRuntime.response_task | Can't handle overlapping user/agent speech |
| TTS warmup before each sentence | _warm_if_needed | Adds latency if cache miss |

## Target Architecture

### Full-Duplex Pipeline Design

Frontend: Audio Input (Mic) -> WebSocket -> Session Runtime (STT/LLM/TTS workers) -> Audio Output (Speaker)

### Key Changes Required

#### 1. Non-blocking STT Handler
- audio_chunk messages -> accumulate in queue (not buffer)
- Separate _stt_worker coroutine processes queue continuously
- audio_end adds marker to queue, doesn't block
- STT results sent via callback to WebSocket output

#### 2. Multi-Turn Concurrent Processing
- SessionRuntime tracks multiple response_task s (not just one)
- Each turn gets a unique turn_id for cancellation
- New interrupt -> cancel specific turn_id, not all

#### 3. Immediate TTS Streaming
- LLM tokens immediately sent to TTS (not waiting for sentence boundaries)
- TTS worker handles partial text chunks
- First audio output within ~500ms of LLM first token

#### 4. Parallel TTS Sentence Processing
- Multiple TTS workers process sentences in parallel
- Sentence N+1 starts before N completes (pipelining)
- Use hedge racing across all sentences

#### 5. Full-Duplex WebSocket Protocol
Input messages: audio_chunk, audio_end, interrupt
Output messages: stt_partial, stt_final, tts_chunk, tts_done

## Implementation Plan

### Phase 1: Refactor Session Runtime
1. Replace audio_buffer with audio_queue
2. Add turn_id tracking per response
3. Support multiple concurrent response_tasks
4. Add proper cancellation per turn_id

### Phase 2: Concurrent STT Worker
1. Create _stt_worker coroutine that continuously processes audio_queue
2. audio_chunk -> put in queue, audio_end -> put marker
3. STT results via callback (not return value)
4. Non-blocking WebSocket handler

### Phase 3: Streaming TTS Integration
1. Modify _handle_candidate_text to stream tokens immediately
2. Remove sentence boundary wait
3. TTS worker handles partial text chunks
4. First chunk latency < 1s target

### Phase 4: Parallel TTS Pipeline
1. Add concurrent sentence processing
2. Multiple TTS workers for overlapping synthesis
3. Hedge racing across workers

### Phase 5: Quality Assurance
1. Test full-duplex scenarios
2. Measure latency (STT->LLM->TTS chain)
3. Verify no memory leaks or race conditions
4. Load test concurrent turns

## Quality Metrics

| Metric | Target | Current |
|--------|--------|---------|
| First audio latency | < 1.5s | ~4s |
| Full response latency | < 5s | ~8-10s |
| Concurrent turns | 3+ overlapping | 1 |
| Audio overlap | User/AI can interleave | Sequential |
| TTS quality | Natural, no artifacts | Good |

## Files to Modify

1. backend/app/ws/interview_ws.py - Core refactor (40%)
2. backend/app/services/stt_service.py - Add callback-based async API
3. backend/app/services/tts_service.py - Streaming + parallel workers
4. backend/app/agents/interviewer_agent.py - Streaming token output
5. backend/app/config.py - New settings for parallel workers, timeouts

## Success Criteria

- [ ] User can interrupt AI mid-sentence, AI responds to new input
- [ ] AI starts speaking within 1.5s of user finishing
- [ ] Multiple overlapping conversations handled
- [ ] No blocking WebSocket operations during STT
- [ ] TTS processes sentences in parallel
- [ ] All quality tests pass

from __future__ import annotations

import asyncio
import base64
import json
import logging
import math
import time
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.agents.interviewer_agent import InterviewerAgent
from app.config import settings
from app.core.security import decode_token
from app.database import AsyncSessionLocal
from app.models.behavior_log import BehaviorLog
from app.models.message import ConversationMessage, MessageRole
from app.models.session import InterviewSession
from app.services.stt_service import stt_service
from app.services.tts_metrics_service import tts_metrics_service
from app.services.tts_service import tts_service
from app.services.vision_service import vision_service

router = APIRouter()
logger = logging.getLogger(__name__)

_TTS_END_MARKERS = {"。", "！", "？", "!", "?", ";", "；", "\n"}
_TTS_SOFT_SPLIT_MARKERS = {"，", ",", "、", "：", ":", " "}
_TTS_MIN_HARD_CHARS = 3
_TTS_SOFT_SPLIT_TRIGGER_CHARS = 12
_TTS_FORCE_SPLIT_CHARS = 30
_TTS_FORCE_SPLIT_AT = 18
_TTS_FIRST_PCM_FLUSH_BYTES = 48
_TTS_PCM_FLUSH_BYTES = 12_000
_TTS_FIRST_SEGMENT_TARGET_CHARS = 2
_TTS_FIRST_SEGMENT_MAX_CHARS = 3
_TTS_STREAM_SEGMENT_TARGET_CHARS = 9
_TTS_STREAM_SEGMENT_MAX_CHARS = 16
_TTS_PREWARM_SESSION_COOLDOWN_SECONDS = 1.0
_LAST_TTS_PREWARM_AT = 0.0
_TTS_MAX_CONCURRENT_WORKERS = 3

# Pipeline parallel processing settings (T12)
# Enable overlapping STT processing with LLM inference for CUDA backends
_PIPELINE_PARALLEL_ENABLED: bool = True
_PIPELINE_STT_CHUNK_SIZE_MS: int = 1000  # Process STT in 1s chunks for overlap


@dataclass
class TurnContext:
    turn_id: str
    response_task: asyncio.Task[None] | None = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    is_active: bool = False


@dataclass
class SessionRuntime:
    websocket: WebSocket
    session_id: UUID
    agent: InterviewerAgent
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    # Full-duplex: audio queue instead of buffer
    audio_queue: asyncio.Queue[tuple[bytes, int] | None] = field(default_factory=asyncio.Queue)
    sample_rate: int = 16000
    # Multi-turn support
    turns: dict[str, TurnContext] = field(default_factory=dict)
    current_turn_id: str = ""
    closed: bool = False
    # STT worker task
    _stt_worker_task: asyncio.Task[None] | None = None

    async def send_json(self, payload: dict[str, Any]) -> None:
        if self.closed:
            return
        async with self.send_lock:
            await self.websocket.send_json(payload)

    async def start_stt_worker(self) -> None:
        """Start the background STT worker coroutine."""
        if self._stt_worker_task is None or self._stt_worker_task.done():
            self._stt_worker_task = asyncio.create_task(self._run_stt_worker())

    async def _run_stt_worker(self) -> None:
        """Background coroutine that continuously processes audio from queue.

        For CUDA backends (faster-whisper-cuda), uses chunked processing to overlap
        STT preprocessing with LLM inference. This reduces effective E2E latency.
        """
        accumulated_pcm = bytearray()
        sample_rate = self.sample_rate
        # For CUDA backends: process in chunks for overlap
        # Chunk size for 16kHz mono PCM: 16000 samples/s * 1s = 16000 bytes
        _CHUNK_BYTES = 16000  # 1 second of audio at 16kHz mono

        while not self.closed:
            try:
                item = await asyncio.wait_for(
                    self.audio_queue.get(),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                # Check for turn cancellation periodically
                continue

            if item is None:
                # Poison pill - audio stream ended
                if accumulated_pcm:
                    # Final transcription
                    await self._process_stt(accumulated_pcm, sample_rate)
                    accumulated_pcm.clear()
                break

            chunk, rate = item
            accumulated_pcm.extend(chunk)
            sample_rate = rate

            # Pipeline parallel processing: start LLM as soon as we have a
            # complete chunk transcribed. This overlaps STT with LLM inference.
            if _PIPELINE_PARALLEL_ENABLED and len(accumulated_pcm) >= _CHUNK_BYTES:
                turn_id = self.current_turn_id
                turn = self.turns.get(turn_id) if turn_id else None
                if turn and not turn.cancel_event.is_set():
                    # Copy bytes to avoid race condition with shared buffer
                    pcm_copy = bytes(accumulated_pcm)
                    accumulated_pcm.clear()
                    # Run STT in background to not block audio capture
                    asyncio.create_task(self._process_stt_async(pcm_copy, sample_rate, turn_id))

    async def _process_stt_async(
        self,
        pcm_bytes: bytes,
        sample_rate: int,
        turn_id: str,
    ) -> None:
        """Process STT asynchronously and start LLM when complete.

        This runs STT in a background task, allowing audio capture to continue.
        Once STT returns, LLM inference starts immediately (overlapping with
        continued audio capture if the user is still speaking).
        """
        if not pcm_bytes:
            return

        # Security check: only process if this is still the current turn
        # This prevents late STT results from triggering LLM for an old turn
        # when a new turn has already started
        if turn_id != self.current_turn_id:
            logger.debug("STT async skipped: turn_id=%s current=%s", turn_id, self.current_turn_id)
            return

        turn = self.turns.get(turn_id) if turn_id else None
        if turn and turn.cancel_event.is_set():
            return

        try:
            final_text = ""
            async for event_type, text in stt_service.transcribe_stream_events(
                bytes(pcm_bytes),
                sample_rate,
            ):
                if turn and turn.cancel_event.is_set():
                    return
                if event_type == "partial":
                    await self.send_json({"type": "stt_partial", "text": text, "turn_id": turn_id})
                    continue
                if event_type == "final":
                    final_text = text

            if final_text.strip():
                await self.send_json({"type": "stt_final", "text": final_text, "turn_id": turn_id})
                # Only start response if not already running for this turn
                if turn and not turn.cancel_event.is_set():
                    existing_turn = self.turns.get(turn_id)
                    if existing_turn and existing_turn.response_task and not existing_turn.response_task.done():
                        # Response already running - don't restart
                        pass
                    else:
                        # Key optimization: start LLM immediately after STT completes
                        # This overlaps with any remaining audio capture
                        await self.start_response(final_text, turn_id)
        except Exception as exc:
            logger.exception("STT async processing failed session=%s error=%s", self.session_id, exc)
            await self.send_json({
                "type": "error",
                "code": "STT_FAILED",
                "message": "语音识别失败",
            })

    async def _process_stt(self, pcm_bytes: bytes, sample_rate: int) -> None:
        """Process accumulated PCM bytes through STT."""
        if not pcm_bytes:
            return

        turn_id = self.current_turn_id
        turn = self.turns.get(turn_id) if turn_id else None
        if turn and turn.cancel_event.is_set():
            return

        try:
            final_text = ""
            async for event_type, text in stt_service.transcribe_stream_events(
                bytes(pcm_bytes),
                sample_rate,
            ):
                if turn and turn.cancel_event.is_set():
                    return
                if event_type == "partial":
                    await self.send_json({"type": "stt_partial", "text": text, "turn_id": turn_id})
                    continue
                if event_type == "final":
                    final_text = text

            await self.send_json({"type": "stt_final", "text": final_text, "turn_id": turn_id})
            if not final_text.strip():
                return
            if turn and turn.cancel_event.is_set():
                return

            # Start response for this turn
            await self.start_response(final_text, turn_id)
        except Exception as exc:
            logger.exception("STT failed session=%s error=%s", self.session_id, exc)
            await self.send_json({
                "type": "error",
                "code": "STT_FAILED",
                "message": "语音识别失败",
            })

    async def cancel_turn(self, turn_id: str, reason: str) -> None:
        """Cancel a specific turn by ID with full interrupt handling."""
        import time

        interrupt_start = time.perf_counter()

        if turn_id not in self.turns:
            return

        turn = self.turns[turn_id]

        # 1. Cancel STT processing immediately
        if self._stt_worker_task and not self._stt_worker_task.done():
            self._stt_worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._stt_worker_task

        # 2. Cancel LLM inference via cancel event
        turn.cancel_event.set()

        # 3. Cancel TTS streaming via cancel event
        if turn.response_task and not turn.response_task.done():
            turn.response_task.cancel()
            with suppress(asyncio.CancelledError):
                await turn.response_task

        turn.is_active = False

        # 4. Send interrupt_ack to frontend
        interrupt_latency_ms = (time.perf_counter() - interrupt_start) * 1000
        with suppress(RuntimeError):
            await self.send_json({
                "type": "interrupt_ack",
                "reason": reason,
                "turn_id": turn_id,
                "interrupt_latency_ms": round(interrupt_latency_ms, 2),
            })

        # Also send tts_interrupted for backward compatibility
        with suppress(RuntimeError):
            await self.send_json({"type": "tts_interrupted", "reason": reason, "turn_id": turn_id})

        if self.current_turn_id == turn_id:
            self.current_turn_id = ""

    async def start_response(self, text: str, turn_id: str | None = None) -> None:
        """Start a response task for given text."""
        if turn_id is None:
            turn_id = uuid.uuid4().hex

        # Cancel any existing turn
        if self.current_turn_id and self.current_turn_id != turn_id:
            await self.cancel_turn(self.current_turn_id, "new_response")

        # Create new turn context
        turn = TurnContext(turn_id=turn_id, is_active=True)
        self.turns[turn_id] = turn
        self.current_turn_id = turn_id

        turn.response_task = asyncio.create_task(
            _handle_candidate_text(self, text, turn_id, turn.cancel_event)
        )

    async def start_audio_turn(self, pcm_bytes: bytes, sample_rate: int, turn_id: str | None = None) -> None:
        """Start an audio transcription turn."""
        if turn_id is None:
            turn_id = uuid.uuid4().hex

        # Cancel existing current turn
        if self.current_turn_id:
            await self.cancel_turn(self.current_turn_id, "new_audio_turn")

        # Create turn context
        turn = TurnContext(turn_id=turn_id, is_active=True)
        self.turns[turn_id] = turn
        self.current_turn_id = turn_id

        # Queue audio for processing
        await self.audio_queue.put((pcm_bytes, sample_rate))

    async def end_audio_turn(self) -> None:
        """Signal end of audio input - sends None to queue to trigger processing."""
        await self.audio_queue.put(None)


@router.websocket("/interview/{session_id}")
async def interview_socket(
    websocket: WebSocket,
    session_id: UUID,
    token: str | None = Query(default=None),
) -> None:
    # Must accept() before any send_json/close calls per WebSocket protocol
    await websocket.accept()

    if token is None:
        await websocket.send_json(
            {"type": "error", "code": "UNAUTHORIZED", "message": "Token required"}
        )
        await websocket.close(code=4401)
        return

    token_payload = decode_token(token)
    if token_payload is None:
        await websocket.send_json(
            {"type": "error", "code": "UNAUTHORIZED", "message": "Invalid or expired token"}
        )
        await websocket.close(code=4401)
        return

    user_id = token_payload.get("sub")

    async with AsyncSessionLocal() as db:
        session = await db.get(InterviewSession, session_id)
        if session is None:
            await websocket.send_json(
                {"type": "error", "code": "SESSION_NOT_FOUND", "message": "Session not found"}
            )
            await websocket.close(code=4404)
            return

        if str(session.user_id) != user_id:
            await websocket.send_json(
                {"type": "error", "code": "FORBIDDEN", "message": "You don't have access to this session"}
            )
            await websocket.close(code=4403)
            return

    runtime = SessionRuntime(
        websocket=websocket,
        session_id=session_id,
        agent=InterviewerAgent(),
    )

    # Start the STT worker
    await runtime.start_stt_worker()

    try:
        while True:
            raw = await websocket.receive_text()
            msg_payload = json.loads(raw)
            msg_type = msg_payload.get("type")

            if msg_type == "ping":
                await runtime.send_json({"type": "pong"})
                continue

            if msg_type == "interrupt":
                turn_id = msg_payload.get("turn_id", runtime.current_turn_id)
                if turn_id:
                    await runtime.cancel_turn(turn_id, str(msg_payload.get("reason") or "client_interrupt"))
                continue

            if msg_type == "candidate_message":
                text = str(msg_payload.get("text", "")).strip()
                turn_id = msg_payload.get("turn_id")
                if text:
                    await runtime.start_response(text, turn_id)
                continue

            if msg_type == "audio_chunk":
                b64_audio = msg_payload.get("data")
                incoming_rate = int(msg_payload.get("sample_rate", runtime.sample_rate))
                if not isinstance(b64_audio, str):
                    continue

                try:
                    chunk = base64.b64decode(b64_audio.encode("utf-8"))
                    await runtime.audio_queue.put((chunk, incoming_rate))
                    runtime.sample_rate = incoming_rate
                except Exception as exc:
                    logger.warning("audio_chunk decode failed: %s", exc)
                continue

            if msg_type == "audio_end":
                turn_id = msg_payload.get("turn_id")
                # Signal end of audio - triggers STT processing
                await runtime.end_audio_turn()
                # STT worker will create turn and start response
                continue

            if msg_type == "behavior_frame":
                await _handle_behavior_frame(runtime, msg_payload)
                continue

            await runtime.send_json(
                {"type": "error", "code": "UNSUPPORTED_TYPE", "message": "Unsupported message type"}
            )

    except WebSocketDisconnect:
        runtime.closed = True
        if runtime._stt_worker_task:
            runtime._stt_worker_task.cancel()
        _behavior_warning_last_sent.pop(str(session_id), None)
        return
    except Exception as exc:
        runtime.closed = True
        with suppress(RuntimeError):
            await runtime.send_json(
                {"type": "error", "code": "WS_INTERNAL_ERROR", "message": str(exc)}
            )
        with suppress(RuntimeError):
            await websocket.close(code=1011)


async def _handle_candidate_text(
    runtime: SessionRuntime,
    text: str,
    response_id: str,
    cancel_event: asyncio.Event,
) -> None:
    session_id = runtime.session_id

    global _LAST_TTS_PREWARM_AT
    now = time.perf_counter()
    if now - _LAST_TTS_PREWARM_AT >= _TTS_PREWARM_SESSION_COOLDOWN_SECONDS:
        _LAST_TTS_PREWARM_AT = now
        with suppress(Exception):
            await tts_service.warmup_if_needed()

    async with AsyncSessionLocal() as db:
        session = await db.get(InterviewSession, session_id)
        if session is None:
            return

        existing = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.turn_index.asc())
        )
        history = existing.scalars().all()
        turn_index = (history[-1].turn_index + 1) if history else 1
        job_role = session.job_role
        resume_profile = session.resume_parsed

        candidate_msg = ConversationMessage(
            session_id=session_id,
            role=MessageRole.candidate,
            content=text,
            turn_index=turn_index,
        )
        db.add(candidate_msg)
        await db.commit()

    dialogue_history = [
        {"role": "assistant" if item.role == MessageRole.interviewer else "user", "content": item.content}
        for item in history
    ]
    dialogue_history.append({"role": "user", "content": text})

    # Full-duplex: Multiple TTS workers for parallel sentence processing
    tts_queue: asyncio.Queue[tuple[str, str] | None] = asyncio.Queue()
    tts_start = time.perf_counter()
    first_audio_latency_ref: list[float | None] = [None]
    tts_chunks = 0
    tts_bytes = 0

    async def _tts_worker(worker_id: int) -> None:
        nonlocal tts_chunks, tts_bytes

        async def _emit_tts_text(tts_input: str) -> bool:
            nonlocal tts_chunks, tts_bytes
            pcm_buffer = bytearray()
            first_flush_sent = False
            first_audio_sent = False

            async def flush_buffer(force: bool = False) -> None:
                nonlocal first_flush_sent, first_audio_sent, tts_chunks, tts_bytes
                if not pcm_buffer:
                    return
                threshold = _TTS_FIRST_PCM_FLUSH_BYTES if not first_flush_sent else _TTS_PCM_FLUSH_BYTES
                if not force and len(pcm_buffer) < threshold:
                    return

                pcm_bytes = bytes(pcm_buffer)
                pcm_buffer.clear()
                if len(pcm_bytes) % 2 != 0:
                    pcm_bytes = pcm_bytes[:-1]
                if not pcm_bytes:
                    return

                first_flush_sent = True
                tts_chunks += 1
                tts_bytes += len(pcm_bytes)

                if not first_audio_sent:
                    first_audio_sent = True
                    if first_audio_latency_ref[0] is None:
                        first_audio_latency_ref[0] = time.perf_counter() - tts_start

                if runtime.current_turn_id != response_id:
                    return

                await runtime.send_json({
                    "type": "tts_audio",
                    "data": base64.b64encode(pcm_bytes).decode("utf-8"),
                    "format": "pcm_s16le",
                    "sample_rate": settings.COSYVOICE_SAMPLE_RATE,
                    "provider": "cosyvoice2-http",
                    "response_id": response_id,
                    "turn_id": response_id,
                })

            try:
                async for pcm_chunk in tts_service.stream_synthesize(tts_input):
                    if cancel_event.is_set() or runtime.current_turn_id != response_id:
                        break
                    pcm_buffer.extend(pcm_chunk)
                    await flush_buffer(force=False)
            except Exception as exc:
                logger.warning("TTS preflight check failed: %s", exc, exc_info=True)
            finally:
                await flush_buffer(force=True)
            return first_flush_sent

        while True:
            item = await tts_queue.get()
            if item is None:
                tts_queue.task_done()
                break

            sentence, seg_id = item
            if cancel_event.is_set():
                tts_queue.task_done()
                continue

            tts_input = tts_service.prepare_text_for_tts(sentence, fallback="")
            plain_len = len(tts_input.strip("，,。！？!?:;； ")) if tts_input else 0
            if tts_input and plain_len < 2:
                tts_queue.task_done()
                continue

            if tts_input:
                try:
                    await _emit_tts_text(tts_input)
                except Exception as exc:
                    logger.warning("TTS emit failed text_len=%s error=%s", len(tts_input), exc)
            tts_queue.task_done()

    # Start multiple TTS workers for parallel processing
    num_workers = min(_TTS_MAX_CONCURRENT_WORKERS, 3)
    tts_workers = [asyncio.create_task(_tts_worker(i)) for i in range(num_workers)]

    queued_sentence_count = 0

    async def _enqueue_tts_sentence(sentence: str, seg_id: str) -> None:
        nonlocal queued_sentence_count
        segments = _split_sentence_for_tts(sentence, first_segment=(queued_sentence_count == 0))
        for segment in segments:
            await tts_queue.put((segment, f"{seg_id}_{queued_sentence_count}"))
            queued_sentence_count += 1

    try:
        llm_start = time.perf_counter()
        first_llm_token_at: float | None = None
        llm_token_chars = 0
        full_text = ""
        sentence_buffer = ""
        seg_counter = 0

        try:
            async for token in runtime.agent.stream_next_question(
                job_role=job_role,
                resume_profile=resume_profile,
                dialogue_history=dialogue_history,
            ):
                if cancel_event.is_set():
                    break

                if token and first_llm_token_at is None:
                    first_llm_token_at = time.perf_counter()
                llm_token_chars += len(token)
                full_text += token

                await runtime.send_json({
                    "type": "llm_token",
                    "token": token,
                    "response_id": response_id,
                    "turn_id": response_id,
                })

                # Stream to TTS immediately without waiting for sentence boundaries
                # This is the key optimization for low-latency first audio
                pending_chunk = token.strip()
                if pending_chunk:
                    seg_counter += 1
                    await _enqueue_tts_sentence(pending_chunk, f"seg_{seg_counter}")

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("LLM stream failed session=%s error=%s", session_id, exc)
            if not full_text.strip() and not cancel_event.is_set():
                full_text = "请继续。"
                seg_counter += 1
                await _enqueue_tts_sentence(full_text, f"seg_{seg_counter}")

        if cancel_event.is_set():
            return

        llm_total_elapsed = time.perf_counter() - llm_start
        llm_first_token_latency = (first_llm_token_at - llm_start) if first_llm_token_at is not None else None
        agent_stats = runtime.agent.pop_last_stream_stats()
        llm_stats_payload = _build_llm_stats_payload(
            raw_stats=agent_stats,
            first_token_seconds=llm_first_token_latency,
            total_seconds=llm_total_elapsed,
            generated_chars=llm_token_chars,
            backend=_resolve_llm_backend_label(runtime.agent),
        )

        llm_text = full_text.strip() or "请继续。"

        async with AsyncSessionLocal() as db:
            interviewer_msg = ConversationMessage(
                session_id=session_id,
                role=MessageRole.interviewer,
                content=llm_text,
                turn_index=turn_index,
            )
            db.add(interviewer_msg)
            await db.commit()

        await runtime.send_json({
            "type": "llm_done",
            "full_text": llm_text,
            "turn_index": turn_index,
            "response_id": response_id,
            "turn_id": response_id,
        })
        await runtime.send_json({"type": "llm_stats", **llm_stats_payload})

        # Signal end of TTS generation
        await tts_queue.join()
        await tts_queue.put(None)
        for w in tts_workers:
            await w

        logger.info("TTS completed session=%s chunks=%s bytes=%s total=%.3fs",
                    session_id, tts_chunks, tts_bytes, time.perf_counter() - tts_start)

        tts_metrics_service.record({
            "session_id": str(session_id),
            "response_id": response_id,
            "tts_first_audio_seconds": first_audio_latency_ref[0],
            "tts_chunks": tts_chunks,
            "tts_bytes": tts_bytes,
            "llm_generated_chars": llm_token_chars,
            "tts_success": tts_chunks > 0,
        })

        if not cancel_event.is_set() and runtime.current_turn_id == response_id:
            await runtime.send_json({"type": "tts_done", "response_id": response_id, "turn_id": response_id})

    except asyncio.CancelledError:
        raise
    finally:
        for w in tts_workers:
            if not w.done():
                await tts_queue.put(None)
                w.cancel()
                with suppress(asyncio.CancelledError):
                    await w


def _build_llm_stats_payload(
    *,
    raw_stats: dict[str, Any],
    first_token_seconds: float | None,
    total_seconds: float,
    generated_chars: int,
    backend: str,
) -> dict[str, Any]:
    def _as_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _ns_to_seconds(value: int | None) -> float | None:
        if value is None or value <= 0:
            return None
        return value / 1_000_000_000

    prompt_eval_count = _as_int(raw_stats.get("prompt_eval_count"))
    eval_count = _as_int(raw_stats.get("eval_count"))
    prompt_eval_seconds = _ns_to_seconds(_as_int(raw_stats.get("prompt_eval_duration")))
    eval_seconds = _ns_to_seconds(_as_int(raw_stats.get("eval_duration")))
    load_seconds = _ns_to_seconds(_as_int(raw_stats.get("load_duration")))
    total_duration_seconds = _ns_to_seconds(_as_int(raw_stats.get("total_duration")))

    generated_tps = None
    if eval_count is not None and eval_seconds is not None and eval_seconds > 0:
        generated_tps = eval_count / eval_seconds

    return {
        key: value
        for key, value in {
            "backend": backend,
            "generated_chars": generated_chars,
            "first_token_seconds": round(first_token_seconds, 3) if first_token_seconds is not None else None,
            "total_seconds": round(total_seconds, 3),
            "done_reason": raw_stats.get("done_reason"),
            "prompt_tokens": prompt_eval_count,
            "generated_tokens": eval_count,
            "prompt_eval_seconds": round(prompt_eval_seconds, 3) if prompt_eval_seconds is not None else None,
            "generation_seconds": round(eval_seconds, 3) if eval_seconds is not None else None,
            "tokens_per_second": round(generated_tps, 2) if generated_tps is not None else None,
            "load_seconds": round(load_seconds, 3) if load_seconds is not None else None,
            "provider_total_seconds": round(total_duration_seconds, 3) if total_duration_seconds is not None else None,
        }.items()
        if value is not None
    }


def _resolve_llm_backend_label(agent: InterviewerAgent) -> str:
    if agent.using_ollama_native:
        return "ollama-native"
    profile_name = getattr(agent, "active_profile_name", "")
    if profile_name == "cloud":
        return "cloud-openai-compatible"
    return "openai-compatible"


def _split_sentence_for_tts(sentence: str, *, first_segment: bool) -> list[str]:
    text = sentence.strip()
    if not text:
        return []

    has_en = any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in text)

    if first_segment:
        target_chars = _TTS_FIRST_SEGMENT_MAX_CHARS_EN if has_en else _TTS_FIRST_SEGMENT_MAX_CHARS
        max_chars = _TTS_FIRST_SEGMENT_MAX_CHARS_EN if has_en else _TTS_FIRST_SEGMENT_MAX_CHARS
    else:
        target_chars = _TTS_STREAM_SEGMENT_MAX_CHARS_EN if has_en else _TTS_STREAM_SEGMENT_MAX_CHARS
        max_chars = _TTS_STREAM_SEGMENT_MAX_CHARS_EN if has_en else _TTS_STREAM_SEGMENT_MAX_CHARS

    if len(text) <= max_chars:
        return [text]

    segments = []
    buffer = text
    while buffer:
        if len(buffer) <= max_chars:
            segments.append(buffer.strip())
            break

        split_pos = -1
        search_end = min(len(buffer), max_chars)
        for idx in range(search_end - 1, target_chars - 2, -1):
            if buffer[idx] in _TTS_SOFT_SPLIT_MARKERS or buffer[idx] in _TTS_END_MARKERS:
                split_pos = idx
                break

        if split_pos < 0:
            split_pos = max_chars - 1

        part = buffer[:split_pos + 1].strip()
        if part:
            segments.append(part)
        buffer = buffer[split_pos + 1:].strip()

    return [seg for seg in segments if seg]


_BEHAVIOR_WARNING_COOLDOWN = 10.0
_behavior_warning_last_sent: dict[str, float] = {}


async def _handle_behavior_frame(runtime: SessionRuntime, payload: dict[str, Any]) -> None:
    session_id = runtime.session_id

    try:
        frame_second = int(payload.get("frame_second", 0))
        eye_contact = float(payload.get("eye_contact_score", 0.5))
        head_pose = float(payload.get("head_pose_score", 0.5))
        gaze_x = payload.get("gaze_x")
        gaze_y = payload.get("gaze_y")
        image_b64 = payload.get("image_base64")

        emotion, confidence = await vision_service.analyze_frame(image_b64)

        async with AsyncSessionLocal() as db:
            item = BehaviorLog(
                session_id=session_id,
                frame_second=frame_second,
                emotion=emotion,
                emotion_confidence=confidence,
                eye_contact_score=eye_contact,
                head_pose_score=head_pose,
                gaze_x=gaze_x,
                gaze_y=gaze_y,
            )
            db.add(item)
            await db.commit()

        warnings = []
        if eye_contact < 0.45:
            warnings.append("视线偏离镜头，请适当回归")
        if head_pose < 0.50:
            warnings.append("头部倾斜较大，请保持正面面对镜头")
        if gaze_x is not None and gaze_y is not None:
            gaze_dist = math.sqrt(gaze_x ** 2 + gaze_y ** 2)
            if gaze_dist > 0.35:
                warnings.append("视线偏移较多，请注视镜头方向")
        if emotion in {"sad", "angry", "fear"}:
            warnings.append("表情偏消极，请保持更积极的面部状态")

        if warnings:
            now = time.time()
            last_sent = _behavior_warning_last_sent.get(str(session_id), 0)
            if now - last_sent >= _BEHAVIOR_WARNING_COOLDOWN:
                _behavior_warning_last_sent[str(session_id)] = now
                await runtime.send_json({
                    "type": "behavior_warning",
                    "warnings": warnings,
                    "frame_second": frame_second,
                })
    except Exception as exc:
        logger.warning("Behavior frame analysis failed session=%s: %s", session_id, exc)
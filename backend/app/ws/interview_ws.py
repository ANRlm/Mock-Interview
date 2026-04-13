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
from typing import Any
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
_TTS_EARLY_SOFT_SPLIT_TRIGGER_CHARS = 4
_TTS_EARLY_FORCE_SPLIT_CHARS = 5
_TTS_EARLY_FORCE_SPLIT_AT = 3
_TTS_FIRST_PCM_FLUSH_BYTES = 384
_TTS_PCM_FLUSH_BYTES = 12_000
_TTS_FIRST_SEGMENT_TARGET_CHARS = 2
_TTS_FIRST_SEGMENT_MAX_CHARS = 3
_TTS_STREAM_SEGMENT_TARGET_CHARS = 9
_TTS_STREAM_SEGMENT_MAX_CHARS = 16
_TTS_FIRST_SEGMENT_TARGET_CHARS_EN = 2
_TTS_FIRST_SEGMENT_MAX_CHARS_EN = 3
_TTS_STREAM_SEGMENT_TARGET_CHARS_EN = 6
_TTS_STREAM_SEGMENT_MAX_CHARS_EN = 12
_TTS_PREWARM_SESSION_COOLDOWN_SECONDS = 14.0
_LAST_TTS_PREWARM_AT = 0.0
_TTS_PREFLIGHT_SAMPLE_TEXT = "好的。"


@dataclass
class SessionRuntime:
    websocket: WebSocket
    session_id: UUID
    agent: InterviewerAgent
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    audio_buffer: bytearray = field(default_factory=bytearray)
    sample_rate: int = 16000
    response_task: asyncio.Task[None] | None = None
    response_cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    active_response_id: str = ""
    closed: bool = False

    async def send_json(self, payload: dict[str, Any]) -> None:
        if self.closed:
            return
        async with self.send_lock:
            await self.websocket.send_json(payload)

    async def cancel_response(self, reason: str) -> None:
        if self.response_task and not self.response_task.done():
            self.response_cancel_event.set()
            self.response_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.response_task
            if not self.closed:
                with suppress(RuntimeError):
                    await self.send_json({"type": "tts_interrupted", "reason": reason})

        self.response_task = None
        self.response_cancel_event = asyncio.Event()
        self.active_response_id = ""

    async def start_response(self, text: str) -> None:
        if self.response_task and not self.response_task.done():
            await self.cancel_response("superseded")
        response_id = uuid.uuid4().hex
        self.active_response_id = response_id
        self.response_task = asyncio.create_task(
            _handle_candidate_text(self, text, response_id)
        )

    async def start_audio_turn(self, pcm_bytes: bytes, sample_rate: int) -> None:
        if self.response_task and not self.response_task.done():
            await self.cancel_response("superseded")
        self.response_task = asyncio.create_task(
            _handle_audio_turn(self, pcm_bytes, sample_rate)
        )


@router.websocket("/interview/{session_id}")
async def interview_socket(
    websocket: WebSocket,
    session_id: UUID,
    token: str | None = Query(default=None),
) -> None:
    if token is None:
        await websocket.send_json(
            {"type": "error", "code": "UNAUTHORIZED", "message": "Token required"}
        )
        await websocket.close(code=4401)
        return

    payload = decode_token(token)
    if payload is None:
        await websocket.send_json(
            {"type": "error", "code": "UNAUTHORIZED", "message": "Invalid or expired token"}
        )
        await websocket.close(code=4401)
        return

    await websocket.accept()

    user_id = payload.get("sub")

    async with AsyncSessionLocal() as db:
        session = await db.get(InterviewSession, session_id)
        if session is None:
            await websocket.send_json(
                {
                    "type": "error",
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found",
                }
            )
            await websocket.close(code=4404)
            return

        if str(session.user_id) != user_id:
            await websocket.send_json(
                {
                    "type": "error",
                    "code": "FORBIDDEN",
                    "message": "You don't have access to this session",
                }
            )
            await websocket.close(code=4403)
            return

    runtime = SessionRuntime(
        websocket=websocket,
        session_id=session_id,
        agent=InterviewerAgent(),
    )

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            msg_type = payload.get("type")

            if msg_type == "ping":
                await runtime.send_json({"type": "pong"})
                continue

            if msg_type == "interrupt":
                await runtime.cancel_response(
                    str(payload.get("reason") or "client_interrupt")
                )
                runtime.audio_buffer.clear()
                continue

            if msg_type == "candidate_message":
                text = str(payload.get("text", "")).strip()
                if text:
                    await runtime.cancel_response("new_candidate_text")
                    await runtime.start_response(text)
                continue

            if msg_type == "audio_chunk":
                b64_audio = payload.get("data")
                incoming_rate = int(payload.get("sample_rate", runtime.sample_rate))
                if not isinstance(b64_audio, str):
                    await runtime.send_json(
                        {
                            "type": "error",
                            "code": "INVALID_AUDIO",
                            "message": "Audio chunk missing",
                        }
                    )
                    continue

                try:
                    chunk = base64.b64decode(b64_audio.encode("utf-8"))
                    runtime.audio_buffer.extend(chunk)
                    runtime.sample_rate = incoming_rate
                except Exception:
                    await runtime.send_json(
                        {
                            "type": "error",
                            "code": "INVALID_AUDIO",
                            "message": "Audio chunk decode failed",
                        }
                    )
                continue

            if msg_type == "audio_end":
                if not runtime.audio_buffer:
                    await runtime.send_json({"type": "stt_final", "text": ""})
                    continue

                pcm_bytes = bytes(runtime.audio_buffer)
                runtime.audio_buffer.clear()

                await runtime.start_audio_turn(pcm_bytes, runtime.sample_rate)
                continue

            if msg_type == "behavior_frame":
                # Real-time behavior analysis and feedback
                await _handle_behavior_frame(runtime, payload)
                continue

            await runtime.send_json(
                {
                    "type": "error",
                    "code": "UNSUPPORTED_TYPE",
                    "message": "Unsupported message type",
                }
            )

    except WebSocketDisconnect:
        runtime.closed = True
        await runtime.cancel_response("disconnect")
        return
    except Exception as exc:
        runtime.closed = True
        await runtime.cancel_response("internal_error")
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
) -> None:
    session_id = runtime.session_id
    cancel_event = runtime.response_cancel_event

    global _LAST_TTS_PREWARM_AT
    now = time.perf_counter()
    if now - _LAST_TTS_PREWARM_AT >= _TTS_PREWARM_SESSION_COOLDOWN_SECONDS:
        _LAST_TTS_PREWARM_AT = now
        with suppress(Exception):
            await tts_service.warmup_if_needed()

    async with AsyncSessionLocal() as db:
        session = await db.get(InterviewSession, session_id)
        if session is None:
            await runtime.send_json(
                {
                    "type": "error",
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found",
                }
            )
            return

        existing = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(
                ConversationMessage.turn_index.asc(),
                ConversationMessage.timestamp.asc(),
            )
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
        {
            "role": "assistant" if item.role == MessageRole.interviewer else "user",
            "content": item.content,
        }
        for item in history
    ]
    dialogue_history.append({"role": "user", "content": text})

    tts_queue: asyncio.Queue[str | None] = asyncio.Queue()
    tts_start = time.perf_counter()
    first_audio_latency_ref: list[float | None] = [None]
    tts_chunks = 0
    tts_bytes = 0

    async def _tts_worker() -> None:
        nonlocal tts_chunks, tts_bytes

        async def _emit_tts_text(tts_input: str) -> bool:
            nonlocal tts_chunks, tts_bytes
            pcm_buffer = bytearray()
            first_flush_sent = False
            first_audio_sent = False

            if (
                queued_sentence_count == 0
                and runtime.active_response_id == response_id
                and not cancel_event.is_set()
            ):
                try:
                    async for _ in tts_service.stream_synthesize(
                        _TTS_PREFLIGHT_SAMPLE_TEXT
                    ):
                        break
                except Exception:
                    pass

            async def flush_buffer(force: bool = False) -> None:
                nonlocal first_flush_sent, first_audio_sent, tts_chunks, tts_bytes
                if not pcm_buffer:
                    return
                threshold = (
                    _TTS_FIRST_PCM_FLUSH_BYTES
                    if not first_flush_sent
                    else _TTS_PCM_FLUSH_BYTES
                )
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
                    logger.info(
                        "TTS first audio sent session=%s response_id=%s text_len=%s latency=%.3fs",
                        session_id,
                        response_id,
                        len(tts_input),
                        time.perf_counter() - tts_start,
                    )
                    if first_audio_latency_ref[0] is None:
                        first_audio_latency_ref[0] = time.perf_counter() - tts_start

                if runtime.active_response_id != response_id:
                    return

                await runtime.send_json(
                    {
                        "type": "tts_audio",
                        "data": base64.b64encode(pcm_bytes).decode("utf-8"),
                        "format": "pcm_s16le",
                        "sample_rate": settings.COSYVOICE_SAMPLE_RATE,
                        "provider": "cosyvoice2-http",
                        "response_id": response_id,
                    }
                )

            async for pcm_chunk in tts_service.stream_synthesize(tts_input):
                if cancel_event.is_set() or runtime.active_response_id != response_id:
                    break
                pcm_buffer.extend(pcm_chunk)
                await flush_buffer(force=False)

            await flush_buffer(force=True)
            return first_flush_sent

        while True:
            sentence = await tts_queue.get()
            if sentence is None:
                tts_queue.task_done()
                break

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
                    logger.warning(
                        "TTS stream failed session=%s text_len=%s error=%s",
                        session_id,
                        len(tts_input),
                        exc,
                    )

            tts_queue.task_done()

    tts_worker_task = asyncio.create_task(_tts_worker())
    queued_sentence_count = 0
    pending_tts_buffer = ""
    verifier = None

    async def _enqueue_tts_sentence(sentence: str) -> None:
        nonlocal queued_sentence_count

        segments = _split_sentence_for_tts(
            sentence,
            first_segment=(queued_sentence_count == 0),
        )
        for segment in segments:
            await tts_queue.put(segment)
            queued_sentence_count += 1

    try:
        llm_start = time.perf_counter()
        first_llm_token_at: float | None = None
        llm_token_chars = 0
        full_text = ""

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
                await runtime.send_json(
                    {"type": "llm_token", "token": token, "response_id": response_id}
                )

                pending_tts_buffer += token
                ready_sentences, pending_tts_buffer = _drain_tts_ready_sentences(
                    pending_tts_buffer,
                    aggressive=(queued_sentence_count == 0),
                )
                for sentence in ready_sentences:
                    await _enqueue_tts_sentence(sentence)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("LLM stream failed session=%s error=%s", session_id, exc)
            if not full_text.strip() and not cancel_event.is_set():
                full_text = "请继续。"
                llm_token_chars = len(full_text)
                await runtime.send_json(
                    {
                        "type": "llm_token",
                        "token": full_text,
                        "response_id": response_id,
                    }
                )
                pending_tts_buffer += full_text
                ready_sentences, pending_tts_buffer = _drain_tts_ready_sentences(
                    pending_tts_buffer,
                    aggressive=(queued_sentence_count == 0),
                )
                for sentence in ready_sentences:
                    await _enqueue_tts_sentence(sentence)

        if cancel_event.is_set():
            return

        llm_total_elapsed = time.perf_counter() - llm_start
        llm_first_token_latency = (
            (first_llm_token_at - llm_start) if first_llm_token_at is not None else None
        )
        agent_stats = runtime.agent.pop_last_stream_stats()
        llm_stats_payload = _build_llm_stats_payload(
            raw_stats=agent_stats,
            first_token_seconds=llm_first_token_latency,
            total_seconds=llm_total_elapsed,
            generated_chars=llm_token_chars,
            backend=_resolve_llm_backend_label(runtime.agent),
        )

        llm_text = full_text.strip() or "请继续。"
        if runtime.active_response_id != response_id:
            return
        tail_sentence = pending_tts_buffer.strip()
        if tail_sentence and len(tail_sentence) < 2 and queued_sentence_count > 0:
            tail_sentence = ""
        if tail_sentence:
            await _enqueue_tts_sentence(tail_sentence)
        if queued_sentence_count == 0:
            await _enqueue_tts_sentence(llm_text)

        async with AsyncSessionLocal() as db:
            interviewer_msg = ConversationMessage(
                session_id=session_id,
                role=MessageRole.interviewer,
                content=llm_text,
                turn_index=turn_index,
            )
            db.add(interviewer_msg)
            await db.commit()

        await runtime.send_json(
            {
                "type": "llm_done",
                "full_text": llm_text,
                "turn_index": turn_index,
                "response_id": response_id,
            }
        )
        await runtime.send_json({"type": "llm_stats", **llm_stats_payload})

        await tts_queue.join()
        await tts_queue.put(None)
        await tts_worker_task

        logger.info(
            "TTS completed session=%s chunks=%s bytes=%s total=%.3fs",
            session_id,
            tts_chunks,
            tts_bytes,
            time.perf_counter() - tts_start,
        )

        tts_metrics_service.record(
            {
                "session_id": str(session_id),
                "response_id": response_id,
                "tts_first_audio_seconds": first_audio_latency_ref[0],
                "tts_chunks": tts_chunks,
                "tts_bytes": tts_bytes,
                "llm_generated_chars": llm_token_chars,
                "tts_success": tts_chunks > 0,
            }
        )

        if not cancel_event.is_set() and runtime.active_response_id == response_id:
            await runtime.send_json({"type": "tts_done", "response_id": response_id})
    except asyncio.CancelledError:
        raise
    finally:
        if not tts_worker_task.done():
            await tts_queue.put(None)
            tts_worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await tts_worker_task


async def _handle_audio_turn(
    runtime: SessionRuntime,
    pcm_bytes: bytes,
    sample_rate: int,
) -> None:
    session_id = runtime.session_id

    try:
        final_text = ""
        async for event_type, text in stt_service.transcribe_stream_events(
            pcm_bytes,
            sample_rate,
        ):
            if runtime.response_cancel_event.is_set():
                return

            if event_type == "partial":
                await runtime.send_json({"type": "stt_partial", "text": text})
                continue

            if event_type == "final":
                final_text = text

        await runtime.send_json({"type": "stt_final", "text": final_text})
        if not final_text.strip() or runtime.response_cancel_event.is_set():
            return

        if runtime.response_task and asyncio.current_task() is runtime.response_task:
            runtime.response_task = None

        await runtime.start_response(final_text)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("STT failed session=%s error=%s", session_id, exc)
        await runtime.send_json(
            {
                "type": "error",
                "code": "STT_FAILED",
                "message": "语音识别失败，请检查 FunASR 服务。",
            }
        )


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


def _build_llm_stats_payload(
    *,
    raw_stats: dict[str, Any],
    first_token_seconds: float | None,
    total_seconds: float,
    generated_chars: int,
    backend: str,
) -> dict[str, Any]:
    prompt_eval_count = _as_int(raw_stats.get("prompt_eval_count"))
    eval_count = _as_int(raw_stats.get("eval_count"))
    prompt_eval_seconds = _ns_to_seconds(_as_int(raw_stats.get("prompt_eval_duration")))
    eval_seconds = _ns_to_seconds(_as_int(raw_stats.get("eval_duration")))
    load_seconds = _ns_to_seconds(_as_int(raw_stats.get("load_duration")))
    total_duration_seconds = _ns_to_seconds(_as_int(raw_stats.get("total_duration")))

    generated_tps = None
    if eval_count is not None and eval_seconds is not None and eval_seconds > 0:
        generated_tps = eval_count / eval_seconds

    payload: dict[str, Any] = {
        "backend": backend,
        "generated_chars": generated_chars,
        "first_token_seconds": round(first_token_seconds, 3)
        if first_token_seconds is not None
        else None,
        "total_seconds": round(total_seconds, 3),
        "done_reason": raw_stats.get("done_reason"),
        "prompt_tokens": prompt_eval_count,
        "generated_tokens": eval_count,
        "prompt_eval_seconds": round(prompt_eval_seconds, 3)
        if prompt_eval_seconds is not None
        else None,
        "generation_seconds": round(eval_seconds, 3)
        if eval_seconds is not None
        else None,
        "tokens_per_second": round(generated_tps, 2)
        if generated_tps is not None
        else None,
        "load_seconds": round(load_seconds, 3) if load_seconds is not None else None,
        "provider_total_seconds": round(total_duration_seconds, 3)
        if total_duration_seconds is not None
        else None,
    }

    return {key: value for key, value in payload.items() if value is not None}


def _resolve_llm_backend_label(agent: InterviewerAgent) -> str:
    if agent.using_ollama_native:
        return "ollama-native"

    profile_name = getattr(agent, "active_profile_name", "")
    if profile_name == "cloud":
        return "cloud-openai-compatible"

    return "openai-compatible"


def _drain_tts_ready_sentences(
    buffer: str,
    *,
    aggressive: bool = False,
) -> tuple[list[str], str]:
    ready: list[str] = []
    start = 0
    soft_trigger = (
        _TTS_EARLY_SOFT_SPLIT_TRIGGER_CHARS
        if aggressive
        else _TTS_SOFT_SPLIT_TRIGGER_CHARS
    )
    force_trigger = (
        _TTS_EARLY_FORCE_SPLIT_CHARS if aggressive else _TTS_FORCE_SPLIT_CHARS
    )
    force_at = _TTS_EARLY_FORCE_SPLIT_AT if aggressive else _TTS_FORCE_SPLIT_AT

    for idx, char in enumerate(buffer):
        if char not in _TTS_END_MARKERS:
            continue

        candidate = buffer[start : idx + 1].strip()
        if candidate and len(candidate) >= _TTS_MIN_HARD_CHARS:
            ready.append(candidate)
            start = idx + 1
            continue

        if candidate:
            continue

        start = idx + 1

    rest = buffer[start:]

    if not ready:
        rest_stripped = rest.strip()
        if len(rest_stripped) >= soft_trigger:
            split_pos = -1
            for idx in range(len(rest) - 1, -1, -1):
                if rest[idx] in _TTS_SOFT_SPLIT_MARKERS:
                    split_pos = idx
                    break

            if split_pos >= _TTS_MIN_HARD_CHARS:
                candidate = rest[: split_pos + 1].strip()
                if candidate:
                    ready.append(candidate)
                rest = rest[split_pos + 1 :]
            elif len(rest_stripped) >= force_trigger:
                candidate = rest[:force_at].strip()
                if candidate:
                    ready.append(candidate)
                rest = rest[force_at:]

    return ready, rest


def _split_sentence_for_tts(sentence: str, *, first_segment: bool) -> list[str]:
    text = sentence.strip()
    if not text:
        return []

    has_en = any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in text)

    target_chars = (
        (
            _TTS_FIRST_SEGMENT_TARGET_CHARS_EN
            if first_segment
            else _TTS_STREAM_SEGMENT_TARGET_CHARS_EN
        )
        if has_en
        else (
            _TTS_FIRST_SEGMENT_TARGET_CHARS
            if first_segment
            else _TTS_STREAM_SEGMENT_TARGET_CHARS
        )
    )
    max_chars = (
        (
            _TTS_FIRST_SEGMENT_MAX_CHARS_EN
            if first_segment
            else _TTS_STREAM_SEGMENT_MAX_CHARS_EN
        )
        if has_en
        else (
            _TTS_FIRST_SEGMENT_MAX_CHARS
            if first_segment
            else _TTS_STREAM_SEGMENT_MAX_CHARS
        )
    )

    if len(text) <= max_chars:
        return [text]

    segments: list[str] = []
    buffer = text
    while buffer:
        if len(buffer) <= max_chars:
            segments.append(buffer.strip())
            break

        split_pos = -1
        search_end = min(len(buffer), max_chars)
        for idx in range(search_end - 1, target_chars - 2, -1):
            if (
                buffer[idx] in _TTS_SOFT_SPLIT_MARKERS
                or buffer[idx] in _TTS_END_MARKERS
            ):
                split_pos = idx
                break

        if split_pos < 0:
            split_pos = max_chars - 1

        part = buffer[: split_pos + 1].strip()
        if part:
            segments.append(part)
        buffer = buffer[split_pos + 1 :].strip()

    return [seg for seg in segments if seg]


_BEHAVIOR_WARNING_COOLDOWN = 10.0
_behavior_warning_last_sent: dict[str, float] = {}


async def _handle_behavior_frame(
    runtime: SessionRuntime,
    payload: dict[str, Any],
) -> None:
    """Handle real-time behavior frame from frontend MediaPipe analysis."""
    session_id = runtime.session_id

    try:
        frame_second = int(payload.get("frame_second", 0))
        eye_contact = float(payload.get("eye_contact_score", 0.5))
        head_pose = float(payload.get("head_pose_score", 0.5))
        gaze_x = payload.get("gaze_x")
        gaze_y = payload.get("gaze_y")
        image_b64 = payload.get("image_base64")

        # Analyze emotion from frame
        emotion, confidence = await vision_service.analyze_frame(image_b64)

        # Persist to DB
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

        # Send real-time feedback if scores are low
        warnings: list[str] = []
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
            last_sent = _behavior_warning_last_sent.get(session_id, 0)
            if now - last_sent >= _BEHAVIOR_WARNING_COOLDOWN:
                _behavior_warning_last_sent[session_id] = now
                await runtime.send_json({
                    "type": "behavior_warning",
                    "warnings": warnings,
                    "frame_second": frame_second,
                })
    except Exception as exc:
        logger.warning("Behavior frame analysis failed session=%s: %s", session_id, exc)

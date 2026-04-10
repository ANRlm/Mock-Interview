from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import time
import wave
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.agents.interviewer_agent import InterviewerAgent
from app.agents.verifier_agent import VerifierAgent
from app.database import AsyncSessionLocal
from app.models.message import ConversationMessage, MessageRole
from app.models.session import InterviewSession
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service

router = APIRouter()
logger = logging.getLogger(__name__)

_TTS_END_MARKERS = {"。", "！", "？", "!", "?", ";", "；", "\n"}
_TTS_SOFT_SPLIT_MARKERS = {"，", ",", "、", "：", ":", " "}
_TTS_MIN_HARD_CHARS = 6
_TTS_SOFT_SPLIT_TRIGGER_CHARS = 24
_TTS_FORCE_SPLIT_CHARS = 42
_TTS_FORCE_SPLIT_AT = 28
_TTS_EARLY_SOFT_SPLIT_TRIGGER_CHARS = 18
_TTS_EARLY_FORCE_SPLIT_CHARS = 30
_TTS_EARLY_FORCE_SPLIT_AT = 20
_TTS_QUEUE_WAV_BYTES_THRESHOLD = 120_000


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

    async def start_response(self, text: str) -> None:
        if self.response_task and not self.response_task.done():
            await self.cancel_response("superseded")
        self.response_task = asyncio.create_task(_handle_candidate_text(self, text))

    async def start_audio_turn(self, pcm_bytes: bytes, sample_rate: int) -> None:
        if self.response_task and not self.response_task.done():
            await self.cancel_response("superseded")
        self.response_task = asyncio.create_task(
            _handle_audio_turn(self, pcm_bytes, sample_rate)
        )


@router.websocket("/interview/{session_id}")
async def interview_socket(websocket: WebSocket, session_id: UUID) -> None:
    await websocket.accept()

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


async def _handle_candidate_text(runtime: SessionRuntime, text: str) -> None:
    session_id = runtime.session_id
    cancel_event = runtime.response_cancel_event

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
    tts_chunks = 0
    tts_bytes = 0

    async def _tts_worker() -> None:
        nonlocal tts_chunks, tts_bytes

        while True:
            sentence = await tts_queue.get()
            if sentence is None:
                tts_queue.task_done()
                break

            if cancel_event.is_set():
                tts_queue.task_done()
                continue

            tts_input = tts_service.prepare_text_for_tts(sentence, fallback="")
            if tts_input:
                try:
                    async for pcm_chunk in tts_service.stream_synthesize(tts_input):
                        if cancel_event.is_set():
                            break

                        wav_chunk = tts_service.pcm_chunk_to_wav(pcm_chunk)
                        if not wav_chunk:
                            continue

                        tts_chunks += 1
                        tts_bytes += len(wav_chunk)
                        for playable_wav in _split_wav_for_playback(wav_chunk):
                            await runtime.send_json(
                                {
                                    "type": "tts_audio",
                                    "data": base64.b64encode(playable_wav).decode(
                                        "utf-8"
                                    ),
                                    "format": "wav",
                                    "provider": "cosyvoice2-http",
                                }
                            )
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
    verifier = VerifierAgent()

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
                await runtime.send_json({"type": "llm_token", "token": token})

                pending_tts_buffer += token
                ready_sentences, pending_tts_buffer = _drain_tts_ready_sentences(
                    pending_tts_buffer,
                    aggressive=(queued_sentence_count == 0),
                )
                for sentence in ready_sentences:
                    await tts_queue.put(sentence)
                    queued_sentence_count += 1
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("LLM stream failed session=%s error=%s", session_id, exc)
            if not full_text.strip() and not cancel_event.is_set():
                full_text = "请继续。"
                llm_token_chars = len(full_text)
                await runtime.send_json({"type": "llm_token", "token": full_text})
                pending_tts_buffer += full_text
                ready_sentences, pending_tts_buffer = _drain_tts_ready_sentences(
                    pending_tts_buffer,
                    aggressive=(queued_sentence_count == 0),
                )
                for sentence in ready_sentences:
                    await tts_queue.put(sentence)
                    queued_sentence_count += 1

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
        try:
            verified = await verifier.verify_question(llm_text)
            if not verified.get("approved", True):
                rewritten = str(verified.get("rewritten_question") or "").strip()
                if rewritten:
                    llm_text = rewritten
        except Exception:
            pass
        tail_sentence = pending_tts_buffer.strip()
        if tail_sentence:
            await tts_queue.put(tail_sentence)
            queued_sentence_count += 1
        if queued_sentence_count == 0:
            await tts_queue.put(llm_text)
            queued_sentence_count += 1

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
            {"type": "llm_done", "full_text": llm_text, "turn_index": turn_index}
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

        if not cancel_event.is_set():
            await runtime.send_json({"type": "tts_done"})
    except asyncio.CancelledError:
        raise
    finally:
        if not tts_worker_task.done():
            await tts_queue.put(None)
            tts_worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await tts_worker_task


def _split_wav_for_playback(wav_bytes: bytes) -> list[bytes]:
    if len(wav_bytes) <= _TTS_QUEUE_WAV_BYTES_THRESHOLD:
        return [wav_bytes]

    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as src:
            channels = src.getnchannels()
            sample_width = src.getsampwidth()
            sample_rate = src.getframerate()
            frame_chunk = max(
                1,
                _TTS_QUEUE_WAV_BYTES_THRESHOLD // max(channels * sample_width, 1),
            )

            chunks: list[bytes] = []
            while True:
                frames = src.readframes(frame_chunk)
                if not frames:
                    break

                out = io.BytesIO()
                with wave.open(out, "wb") as dst:
                    dst.setnchannels(channels)
                    dst.setsampwidth(sample_width)
                    dst.setframerate(sample_rate)
                    dst.writeframes(frames)
                chunks.append(out.getvalue())

            return chunks or [wav_bytes]
    except Exception:
        return [wav_bytes]


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

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.database import AsyncSessionLocal
from app.models.session import InterviewSession
from app.services import tts_service

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


@dataclass
class TtsRuntime:
    websocket: WebSocket
    session_id: UUID
    user_id: str
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
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
            _handle_text_input(self, text, response_id)
        )


@router.websocket("/tts/{session_id}")
async def tts_socket(
    websocket: WebSocket,
    session_id: UUID,
    token: str | None = Query(default=None),
) -> None:
    # JWT Authentication
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

    # Session ownership validation
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

    runtime = TtsRuntime(
        websocket=websocket,
        session_id=session_id,
        user_id=user_id,
    )

    try:
        while True:
            raw = await websocket.receive_text()
            payload_data = json.loads(raw)
            msg_type = payload_data.get("type")

            if msg_type == "ping":
                await runtime.send_json({"type": "pong"})
                continue

            if msg_type == "interrupt":
                await runtime.cancel_response(
                    str(payload_data.get("reason") or "client_interrupt")
                )
                continue

            if msg_type == "text_input":
                text = str(payload_data.get("text", "")).strip()
                response_id = payload_data.get("response_id", "")
                if text:
                    await runtime.cancel_response("new_text_input")
                    if response_id:
                        runtime.active_response_id = response_id
                    await runtime.start_response(text)
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


async def _handle_text_input(
    runtime: TtsRuntime,
    text: str,
    response_id: str,
) -> None:
    """Handle text input and stream TTS audio."""
    tts_start = time.perf_counter()
    first_audio_sent = False

    async def _emit_tts_text(tts_input: str) -> bool:
        nonlocal first_audio_sent
        pcm_buffer = bytearray()

        async def flush_buffer(force: bool = False) -> None:
            nonlocal first_audio_sent
            if not pcm_buffer:
                return

            threshold = _TTS_FIRST_PCM_FLUSH_BYTES if not first_audio_sent else _TTS_PCM_FLUSH_BYTES
            if not force and len(pcm_buffer) < threshold:
                return

            pcm_bytes = bytes(pcm_buffer)
            pcm_buffer.clear()
            if len(pcm_bytes) % 2 != 0:
                pcm_bytes = pcm_bytes[:-1]
            if not pcm_bytes:
                return

            first_audio_sent = True

            if runtime.active_response_id != response_id:
                return

            await runtime.send_json(
                {
                    "type": "tts_audio",
                    "data": base64.b64encode(pcm_bytes).decode("utf-8"),
                    "format": "pcm_s16le",
                    "sample_rate": 16000,
                    "provider": "cosyvoice2-http",
                    "response_id": response_id,
                }
            )

        async for pcm_chunk in tts_service.stream_synthesize(tts_input):
            if runtime.active_response_id != response_id:
                break
            pcm_buffer.extend(pcm_chunk)
            await flush_buffer(force=False)

        await flush_buffer(force=True)
        return first_audio_sent

    # Split text into sentences for TTS
    sentences = _split_for_tts(text)
    for sentence in sentences:
        if runtime.active_response_id != response_id:
            return

        tts_input = tts_service.prepare_text_for_tts(sentence, fallback="")
        plain_len = len(tts_input.strip("，,。！？!?:;； ")) if tts_input else 0
        if tts_input and plain_len < 2:
            continue

        if tts_input:
            try:
                await _emit_tts_text(tts_input)
            except Exception as exc:
                logger.warning(
                    "TTS stream failed session=%s text_len=%s error=%s",
                    runtime.session_id,
                    len(tts_input),
                    exc,
                )

    if runtime.active_response_id == response_id:
        await runtime.send_json({"type": "tts_done", "response_id": response_id})

    logger.info(
        "TTS completed session=%s response_id=%s total=%.3fs",
        runtime.session_id,
        response_id,
        time.perf_counter() - tts_start,
    )


def _split_for_tts(text: str) -> list[str]:
    """Split text into TTS-ready sentences."""
    if not text:
        return []

    ready: list[str] = []
    start = 0

    for idx, char in enumerate(text):
        if char not in _TTS_END_MARKERS:
            continue

        candidate = text[start: idx + 1].strip()
        if candidate and len(candidate) >= _TTS_MIN_HARD_CHARS:
            ready.append(candidate)
            start = idx + 1
            continue

        if candidate:
            continue

        start = idx + 1

    rest = text[start:].strip()
    if rest and len(rest) >= _TTS_MIN_HARD_CHARS:
        ready.append(rest)

    return ready

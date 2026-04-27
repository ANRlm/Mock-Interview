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
from sqlalchemy import select

from app.core.security import decode_token
from app.database import AsyncSessionLocal
from app.models.session import InterviewSession
from app.services.stt_service import stt_service

router = APIRouter()
logger = logging.getLogger(__name__)


@dataclass
class SttRuntime:
    websocket: WebSocket
    session_id: UUID
    user_id: str
    audio_buffer: bytearray = field(default_factory=bytearray)
    sample_rate: int = 16000
    closed: bool = False

    async def send_json(self, payload: dict[str, Any]) -> None:
        if self.closed:
            return
        await self.websocket.send_json(payload)


@router.websocket("/stt/{session_id}")
async def stt_socket(
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

    runtime = SttRuntime(
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

            if msg_type == "audio_chunk":
                b64_audio = payload_data.get("data")
                incoming_rate = int(payload_data.get("sample_rate", runtime.sample_rate))
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

                # Process STT
                try:
                    final_text = ""
                    async for event_type, text in stt_service.transcribe_stream_events(
                        pcm_bytes,
                        runtime.sample_rate,
                    ):
                        if event_type == "partial":
                            await runtime.send_json({"type": "stt_partial", "text": text})
                            continue
                        if event_type == "final":
                            final_text = text

                    await runtime.send_json({"type": "stt_final", "text": final_text})
                except Exception as exc:
                    logger.exception("STT failed session=%s error=%s", session_id, exc)
                    await runtime.send_json(
                        {
                            "type": "error",
                            "code": "STT_FAILED",
                            "message": "Speech recognition failed",
                        }
                    )
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
        return
    except Exception as exc:
        runtime.closed = True
        with suppress(RuntimeError):
            await runtime.send_json(
                {"type": "error", "code": "WS_INTERNAL_ERROR", "message": str(exc)}
            )
        with suppress(RuntimeError):
            await websocket.close(code=1011)

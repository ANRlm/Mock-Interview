"""REST endpoint for one-shot audio transcription (used by manual voice input in text mode).

Accepts a WebM/Ogg audio file upload, converts it to raw PCM using pydub/ffmpeg if
available, then delegates to the STT service. Falls back to forwarding the raw bytes
to FunASR if no audio conversion library is present, which works when FunASR itself
can handle the input format.
"""
from __future__ import annotations

import io
import logging
import struct
import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.interview import _assert_session_owner
from app.database import get_db
from app.models.session import InterviewSession
from app.models.user import User
from app.services.stt_service import stt_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["transcribe"])


def _try_decode_webm_to_pcm(audio_bytes: bytes) -> tuple[bytes, int] | None:
    """Attempt to decode WebM/audio bytes to PCM using pydub (if installed).

    Returns (pcm_bytes, sample_rate) or None if pydub is unavailable.
    """
    try:
        from pydub import AudioSegment  # type: ignore

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            seg = AudioSegment.from_file(tmp_path)
            seg = seg.set_channels(1).set_sample_width(2)  # mono, 16-bit
            pcm = seg.raw_data
            return pcm, seg.frame_rate
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except ImportError:
        return None
    except Exception as exc:
        logger.warning("pydub decode failed: %s", exc)
        return None


def _try_decode_webm_with_av(audio_bytes: bytes) -> tuple[bytes, int] | None:
    """Attempt to decode audio using PyAV (if installed)."""
    try:
        import av  # type: ignore

        buf = io.BytesIO(audio_bytes)
        container = av.open(buf)
        stream = next(s for s in container.streams if s.type == "audio")
        sample_rate = stream.codec_context.sample_rate or 16000

        pcm_chunks: list[bytes] = []
        for frame in container.decode(stream):
            # Convert to 16-bit mono
            arr = frame.to_ndarray(format="s16", layout="mono")
            pcm_chunks.append(arr.tobytes())

        if not pcm_chunks:
            return None
        return b"".join(pcm_chunks), sample_rate
    except ImportError:
        return None
    except Exception as exc:
        logger.warning("PyAV decode failed: %s", exc)
        return None


def _wrap_as_wav(raw_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """Wrap raw PCM bytes into a minimal WAV container for services that need WAV."""
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_bytes)
    return buf.getvalue()


@router.post("/{session_id}/transcribe")
async def transcribe_audio(
    session_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Transcribe an uploaded audio file and return the recognised text.

    Accepts WebM, Ogg, WAV, or any format supported by the configured STT backend.
    The endpoint is used by the manual voice-input feature in text-mode interviews.
    """
    session = await db.get(InterviewSession, session_id)
    _assert_session_owner(session, current_user)

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # Attempt format conversion to raw PCM (best-effort, order: pydub > av > passthrough)
    decoded: tuple[bytes, int] | None = (
        _try_decode_webm_to_pcm(audio_bytes)
        or _try_decode_webm_with_av(audio_bytes)
    )

    try:
        if decoded is not None:
            pcm_bytes, sample_rate = decoded
            _, final_text = await stt_service.transcribe_streaming(pcm_bytes, sample_rate)
        else:
            # Passthrough: send raw bytes and hope the STT backend handles the format.
            # FunASR natively accepts WebM/Ogg when the bytes are sent as PCM stream.
            logger.info(
                "No audio conversion library available; forwarding raw %d bytes to STT",
                len(audio_bytes),
            )
            _, final_text = await stt_service.transcribe_streaming(audio_bytes, 16000)
    except Exception as exc:
        logger.exception("Transcription failed for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="语音识别服务暂不可用，请检查 STT 服务状态。",
        ) from exc

    return {"text": final_text, "session_id": str(session_id)}

from __future__ import annotations

import io
import wave

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.tts_metrics_service import tts_metrics_service
from app.services.tts_service import tts_service
from app.config import settings

router = APIRouter(prefix="/tts", tags=["tts"])


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


@router.post("/speak")
async def speak(
    payload: SpeakRequest,
    _: User = Depends(get_current_user),
) -> Response:
    """Synthesize speech for a text string and return a WAV audio response.

    Used by the manual TTS playback feature (replaying individual messages).
    """
    prepared = tts_service.prepare_text_for_tts(payload.text, fallback="")
    if not prepared or not prepared.strip("，,。！？!?:;； "):
        raise HTTPException(status_code=400, detail="Text too short or empty after normalisation")

    pcm_chunks: list[bytes] = []
    try:
        async for chunk in tts_service.stream_synthesize(prepared):
            if chunk:
                pcm_chunks.append(chunk)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TTS service unavailable",
        ) from exc

    if not pcm_chunks:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No audio generated")

    raw_pcm = b"".join(pcm_chunks)
    # Ensure even byte count for 16-bit PCM
    if len(raw_pcm) % 2 != 0:
        raw_pcm = raw_pcm[:-1]

    # Wrap raw PCM in a WAV container so the browser <Audio> tag can play it
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(settings.COSYVOICE_SAMPLE_RATE)
        wf.writeframes(raw_pcm)

    return Response(
        content=buf.getvalue(),
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=speech.wav"},
    )


@router.get("/metrics")
async def get_tts_metrics() -> dict:
    return tts_metrics_service.summary()


@router.delete("/metrics")
async def reset_tts_metrics() -> dict:
    tts_metrics_service.clear()
    return {"ok": True}

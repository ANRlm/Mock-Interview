from __future__ import annotations

import io
import logging
import wave
from collections.abc import AsyncIterator

import httpx

from app.config import settings
from app.services.audio_utils import resample_pcm_s16le as _resample_pcm_s16le

logger = logging.getLogger(__name__)

_TARGET_SAMPLE_RATE = 16000


class SenseVoiceSTTService:
    def __init__(self) -> None:
        self._base_url = settings.SENSEVOICE_BASE_URL.rstrip("/")
        self._api_key = settings.SENSEVOICE_API_KEY
        self._timeout = float(settings.SENSEVOICE_TIMEOUT_SECONDS)

    async def ensure_model_ready(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/healthz")
                if response.status_code < 400:
                    return True
        except Exception as e:
            logger.warning(
                "SenseVoice health check failed (host=%s): %s",
                self._base_url,
                repr(e),
            )
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/docs")
                if response.status_code < 400:
                    return True
        except Exception as e:
            logger.warning(
                "SenseVoice docs endpoint check failed (host=%s): %s",
                self._base_url,
                repr(e),
            )
        logger.warning(
            "SenseVoice health endpoint unavailable, runtime validation required"
        )
        return False

    async def transcribe_streaming(
        self,
        pcm_bytes: bytes,
        sample_rate: int = _TARGET_SAMPLE_RATE,
    ) -> tuple[list[str], str]:
        partials: list[str] = []
        final_text = ""
        async for event_type, text in self.transcribe_stream_events(
            pcm_bytes,
            sample_rate,
        ):
            if event_type == "partial":
                partials.append(text)
            elif event_type == "final":
                final_text = text

        if not final_text:
            raise RuntimeError("stt_transcription_empty")

        return self._build_partials(partials, final_text), final_text

    async def transcribe_stream_events(
        self,
        pcm_bytes: bytes,
        sample_rate: int = _TARGET_SAMPLE_RATE,
    ) -> AsyncIterator[tuple[str, str]]:
        if not pcm_bytes:
            return

        normalized_pcm = self._normalize_pcm16_mono(
            pcm_bytes=pcm_bytes,
            source_rate=sample_rate,
            target_rate=_TARGET_SAMPLE_RATE,
        )
        if not normalized_pcm:
            return

        wav_buffer = self._pcm_to_wav(normalized_pcm, _TARGET_SAMPLE_RATE)

        headers = {}
        if self._api_key:
            headers["X-API-Key"] = self._api_key

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                files = {"file": ("audio.wav", wav_buffer.getvalue(), "audio/wav")}
                data = {"lang": "zh"}
                response = await client.post(
                    f"{self._base_url}/asr",
                    files=files,
                    data=data,
                    headers=headers,
                )
                if response.status_code >= 400:
                    logger.error(
                        "SenseVoice API error: status=%s body=%s",
                        response.status_code,
                        response.text,
                    )
                    raise RuntimeError("stt_transcription_failed")

                result = response.json()
                text = result.get("text", "").strip()
                if text:
                    yield ("final", text)
                else:
                    logger.warning("SenseVoice returned empty text")
                    raise RuntimeError("stt_transcription_empty")

        except RuntimeError:
            raise
        except Exception as exc:
            logger.exception(
                "SenseVoice transcription failed: source_rate=%s bytes=%s error=%s",
                sample_rate,
                len(pcm_bytes),
                exc,
            )
            raise RuntimeError("stt_transcription_failed") from exc

    def _normalize_pcm16_mono(
        self,
        *,
        pcm_bytes: bytes,
        source_rate: int,
        target_rate: int,
    ) -> bytes:
        if source_rate <= 0:
            raise RuntimeError("invalid_sample_rate")

        pcm = pcm_bytes
        if len(pcm) % 2 != 0:
            pcm = pcm[:-1]

        if source_rate == target_rate:
            return pcm

        try:
            converted = _resample_pcm_s16le(pcm, source_rate, target_rate)
            logger.info(
                "Resampled PCM from %sHz to %sHz (%s -> %s bytes)",
                source_rate,
                target_rate,
                len(pcm),
                len(converted),
            )
            return converted
        except Exception as exc:
            logger.exception("PCM resample failed: %s", exc)
            raise RuntimeError("pcm_resample_failed") from exc

    def _pcm_to_wav(self, pcm_bytes: bytes, sample_rate: int) -> io.BytesIO:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        buffer.seek(0)
        return buffer

    def _build_partials(self, online_texts: list[str], final_text: str) -> list[str]:
        cleaned: list[str] = []
        for text in online_texts:
            if not text:
                continue
            if cleaned and text == cleaned[-1]:
                continue
            cleaned.append(text)

        if not cleaned:
            preview_len = max(1, min(8, len(final_text)))
            if preview_len >= len(final_text):
                return [final_text]
            return [final_text[:preview_len], final_text]

        if cleaned[-1] != final_text:
            cleaned.append(final_text)
        return cleaned


sensevoice_stt_service = SenseVoiceSTTService()

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx
import websockets

from app.config import settings
from app.services.audio_utils import resample_pcm_s16le as _resample_pcm_s16le
from app.services.sensevoice_stt_service import sensevoice_stt_service

try:
    from app.services.faster_whisper_stt_service import faster_whisper_stt_service
except ImportError:
    faster_whisper_stt_service = None


logger = logging.getLogger(__name__)

_TARGET_SAMPLE_RATE = 16000
_FUNASR_CHUNK_SIZE = [5, 10, 5]
_FUNASR_CHUNK_INTERVAL = 10
_FUNASR_ENCODER_CHUNK_LOOK_BACK = 4
_FUNASR_DECODER_CHUNK_LOOK_BACK = 0


class STTService:
    def __init__(self) -> None:
        self._backend = settings.STT_BACKEND
        self._base_url = settings.FUNASR_BASE_URL.rstrip("/")
        self._health_path = self._normalize_path(settings.FUNASR_HEALTH_PATH)
        self._timeout = float(settings.FUNASR_TIMEOUT_SECONDS)
        self._extra_payload = self._parse_extra_payload(settings.FUNASR_EXTRA_PAYLOAD)

    async def ensure_model_ready(self) -> bool:
        if self._backend == "faster-whisper-cuda":
            if faster_whisper_stt_service is not None:
                try:
                    if await faster_whisper_stt_service.ensure_model_ready():
                        return True
                except Exception:
                    pass
                logger.warning("Faster-Whisper-CUDA not available, falling back to HTTP backend")
            return await self._ensure_http_backend_ready()

        if self._backend == "sensevoice-http":
            return await sensevoice_stt_service.ensure_model_ready()

        if self._backend != "funasr-http":
            logger.warning("Unsupported STT backend: %s", self._backend)
            return False

        return await self._ensure_http_backend_ready()

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
        if self._backend == "faster-whisper-cuda":
            if faster_whisper_stt_service is not None:
                try:
                    async for event_type, text in faster_whisper_stt_service.transcribe_stream_events(
                        pcm_bytes,
                        sample_rate,
                    ):
                        yield event_type, text
                    return
                except Exception as exc:
                    logger.warning("Faster-Whisper-CUDA failed, falling back to HTTP backend: %s", exc)

            # Fall back to funasr-http
            async for event_type, text in self._transcribe_funasr(pcm_bytes, sample_rate):
                yield event_type, text
            return

        if self._backend == "sensevoice-http":
            # Delegate to SenseVoice service
            async for event_type, text in sensevoice_stt_service.transcribe_stream_events(
                pcm_bytes,
                sample_rate,
            ):
                yield event_type, text
            return

        if self._backend != "funasr-http":
            raise RuntimeError(f"Unsupported STT backend: {self._backend}")

        async for event_type, text in self._transcribe_funasr(pcm_bytes, sample_rate):
            yield event_type, text

    def _safe_json_loads(self, raw: str) -> dict | list | None:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

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

    async def _ensure_http_backend_ready(self) -> bool:
        """Check if funasr-http backend is ready."""
        host = self._funasr_host()
        parsed = urlparse(self._base_url)
        configured_port = parsed.port
        ports = (
            tuple(dict.fromkeys((configured_port, 10095, 10096)))
            if configured_port is not None
            else (10095, 10096)
        )

        for port in ports:
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(
                        f"http://{host}:{port}{self._health_path}"
                    )
                    if response.status_code < 400:
                        return True
            except Exception:
                continue

        logger.warning(
            "FunASR health endpoint unavailable, runtime validation required"
        )
        return True

    async def _transcribe_funasr(
        self,
        pcm_bytes: bytes,
        sample_rate: int = _TARGET_SAMPLE_RATE,
    ) -> AsyncIterator[tuple[str, str]]:
        """Transcribe using FunASR HTTP backend (fallback when CUDA fails)."""
        if not pcm_bytes:
            return

        normalized_pcm = self._normalize_pcm16_mono(
            pcm_bytes=pcm_bytes,
            source_rate=sample_rate,
            target_rate=_TARGET_SAMPLE_RATE,
        )
        if not normalized_pcm:
            return

        ws_url = self._funasr_ws_url()
        init_payload = {
            "mode": "2pass",
            "chunk_size": _FUNASR_CHUNK_SIZE,
            "chunk_interval": _FUNASR_CHUNK_INTERVAL,
            "encoder_chunk_look_back": _FUNASR_ENCODER_CHUNK_LOOK_BACK,
            "decoder_chunk_look_back": _FUNASR_DECODER_CHUNK_LOOK_BACK,
            "wav_name": "session_chunk",
            "is_speaking": True,
            "wav_format": "pcm",
            "audio_fs": _TARGET_SAMPLE_RATE,
            "itn": settings.FUNASR_USE_ITN,
            **self._extra_payload,
        }

        partial_texts: list[str] = []
        latest_partial = ""
        final_text = ""

        try:
            async with websockets.connect(ws_url, close_timeout=self._timeout) as ws:
                await ws.send(json.dumps(init_payload, ensure_ascii=False))
                await ws.send(normalized_pcm)
                await ws.send(json.dumps({"is_speaking": False}))

                deadline = time.monotonic() + self._timeout
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break

                    wait_timeout = min(2.0, remaining)
                    try:
                        message = await asyncio.wait_for(
                            ws.recv(), timeout=wait_timeout
                        )
                    except asyncio.TimeoutError:
                        continue

                    if isinstance(message, bytes):
                        continue

                    parsed = self._safe_json_loads(message)
                    if not isinstance(parsed, dict):
                        continue

                    mode = str(parsed.get("mode", ""))
                    text = str(parsed.get("text", "")).strip()
                    if not text:
                        if parsed.get("is_final") is True and final_text:
                            break
                        continue

                    if mode in {"2pass-online", "online"}:
                        partial_texts.append(text)
                        if text != latest_partial:
                            latest_partial = text
                            yield ("partial", text)
                        continue

                    if mode in {"2pass-offline", "offline"}:
                        final_text = text
                        break

                    final_text = text
                    if parsed.get("is_final") is True:
                        break

            if not final_text:
                if latest_partial:
                    logger.warning("FunASR final missing, using latest partial text")
                    final_text = latest_partial
                else:
                    raise RuntimeError("FunASR returned empty final text")

            yield ("final", final_text)
            return
        except Exception as exc:
            logger.exception(
                "FunASR transcription failed: source_rate=%s bytes=%s error=%s",
                sample_rate,
                len(pcm_bytes),
                exc,
            )
            raise RuntimeError("stt_transcription_failed") from exc

    def _funasr_host(self) -> str:
        parsed = urlparse(self._base_url)
        if parsed.hostname:
            return parsed.hostname

        url = self._base_url
        if "://" in url:
            url = url.split("://", 1)[1]
        return url.split("/", 1)[0].split(":", 1)[0]

    def _funasr_ws_url(self) -> str:
        parsed = urlparse(self._base_url)
        host = self._funasr_host()
        scheme = "wss" if parsed.scheme == "https" else "ws"
        port = parsed.port or 10095
        return f"{scheme}://{host}:{port}"

    def _normalize_path(self, path: str) -> str:
        clean = (path or "").strip()
        if not clean:
            return "/"
        if not clean.startswith("/"):
            clean = f"/{clean}"
        return clean

    def _parse_extra_payload(self, raw: str) -> dict[str, object]:
        text = (raw or "").strip()
        if not text:
            return {}
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("FUNASR_EXTRA_PAYLOAD is invalid JSON, ignored")
            return {}
        if not isinstance(value, dict):
            logger.warning("FUNASR_EXTRA_PAYLOAD is not JSON object, ignored")
            return {}
        return value


stt_service = STTService()

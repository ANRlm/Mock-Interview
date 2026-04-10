from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
from collections.abc import AsyncIterator
from io import BytesIO
from pathlib import Path
import wave

import httpx

from app.config import settings


TTS_PROVIDER_COSYVOICE2 = "cosyvoice2-http"


logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self) -> None:
        self._cache_dir = Path(settings.TTS_CACHE_DIR)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._base_url = settings.COSYVOICE_BASE_URL.rstrip("/")
        self._tts_path = self._normalize_path(settings.COSYVOICE_TTS_PATH)
        self._health_path = self._normalize_path(settings.COSYVOICE_HEALTH_PATH)
        timeout_seconds = float(settings.COSYVOICE_TIMEOUT_SECONDS)
        self._timeout = timeout_seconds
        self._stream_timeout = httpx.Timeout(
            connect=min(15.0, timeout_seconds),
            read=max(120.0, timeout_seconds),
            write=max(30.0, timeout_seconds),
            pool=max(30.0, timeout_seconds),
        )
        self._extra_payload = self._parse_extra_payload(
            settings.COSYVOICE_EXTRA_PAYLOAD
        )
        self._fixed_seed = int(settings.COSYVOICE_SEED)
        self._speed = float(settings.COSYVOICE_SPEED)
        self._warm_lock = asyncio.Lock()
        self._warmed_recently_until = 0.0

    async def ensure_ready(self) -> bool:
        if settings.TTS_BACKEND != TTS_PROVIDER_COSYVOICE2:
            logger.warning("Unsupported TTS backend: %s", settings.TTS_BACKEND)
            return False

        endpoint = f"{self._base_url}{self._tts_path}"
        probe_payload = {
            "tts_text": "你好。",
            "spk_id": settings.COSYVOICE_VOICE,
            "seed": self._fixed_seed,
            "speed": self._speed,
            **self._extra_payload,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                health = await client.get(f"{self._base_url}{self._health_path}")
                if health.status_code >= 400:
                    logger.warning(
                        "CosyVoice health check failed: status=%s body=%s",
                        health.status_code,
                        health.text[:200],
                    )

                chunk_seen = False
                async with client.stream("POST", endpoint, data=probe_payload) as probe:
                    if probe.status_code >= 400:
                        body = (await probe.aread()).decode("utf-8", errors="ignore")
                        logger.warning(
                            "CosyVoice probe failed endpoint=%s status=%s body=%s",
                            endpoint,
                            probe.status_code,
                            body[:200],
                        )
                        return False

                    async for chunk in probe.aiter_bytes():
                        if chunk:
                            chunk_seen = True
                            break

                if not chunk_seen:
                    logger.warning(
                        "CosyVoice probe returned no audio chunk endpoint=%s", endpoint
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning(
                "CosyVoice health/probe error endpoint=%s error=%s", endpoint, exc
            )
            return False

    def prepare_text_for_tts(self, text: str, *, fallback: str = "请继续。") -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return fallback

        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"```[\s\S]*?```", " ", cleaned)
        cleaned = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"\[([^\]]+)\]\((?:https?://[^)]+)\)", r"\1", cleaned)
        cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
        cleaned = re.sub(r"https?://\S+", " ", cleaned)
        cleaned = re.sub(r"(^|\n)\s{0,3}#{1,6}\s*", r"\1", cleaned)
        cleaned = re.sub(r"(^|\n)\s*>\s*", r"\1", cleaned)
        cleaned = re.sub(r"(^|\n)\s*(?:[-*+]|\d+\.)\s+", r"\1", cleaned)
        cleaned = cleaned.replace("|", " ")
        cleaned = cleaned.replace("*", "")
        cleaned = cleaned.replace("_", "")
        cleaned = cleaned.replace("~", "")
        cleaned = cleaned.replace("\n", "。")
        cleaned = re.sub(r"[\[\]{}<>]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return fallback
        return cleaned

    async def synthesize_with_meta(self, text: str) -> tuple[bytes, str, str]:
        sentence = text.strip() or "请继续。"
        cache_key = self._cache_key(sentence)
        wav_cache_path = self._cache_dir / f"{cache_key}.wav"
        if wav_cache_path.exists():
            logger.debug("TTS cache hit (wav) for text length=%s", len(sentence))
            return wav_cache_path.read_bytes(), "wav", TTS_PROVIDER_COSYVOICE2

        chunks: list[bytes] = []
        async for audio_chunk in self.stream_synthesize(sentence):
            chunks.append(audio_chunk)

        if not chunks:
            raise RuntimeError("CosyVoice stream returned empty audio")

        raw_pcm = b"".join(chunks)
        wav_bytes = self._pcm_to_wav(raw_pcm, settings.COSYVOICE_SAMPLE_RATE)
        wav_cache_path.write_bytes(wav_bytes)
        logger.info(
            "TTS generated provider=%s format=wav bytes=%s",
            TTS_PROVIDER_COSYVOICE2,
            len(wav_bytes),
        )
        return wav_bytes, "wav", TTS_PROVIDER_COSYVOICE2

    async def stream_synthesize(self, text: str) -> AsyncIterator[bytes]:
        if settings.TTS_BACKEND != TTS_PROVIDER_COSYVOICE2:
            raise RuntimeError(f"Unsupported TTS backend: {settings.TTS_BACKEND}")

        sentence = text.strip() or "请继续。"
        await self._warm_if_needed()
        cache_key = self._cache_key(sentence)
        wav_cache_path = self._cache_dir / f"{cache_key}.wav"
        if wav_cache_path.exists():
            logger.debug("TTS stream cache hit (wav) for text length=%s", len(sentence))
            yield wav_cache_path.read_bytes()
            return

        endpoint = f"{self._base_url}{self._tts_path}"
        payload = {
            "tts_text": sentence,
            "spk_id": settings.COSYVOICE_VOICE,
            "seed": self._fixed_seed,
            "speed": self._speed,
            **self._extra_payload,
        }

        attempts = 2
        for attempt in range(1, attempts + 1):
            yielded_any = False
            stream_start = time.perf_counter()
            try:
                async with httpx.AsyncClient(timeout=self._stream_timeout) as client:
                    async with client.stream(
                        "POST", endpoint, data=payload
                    ) as response:
                        if response.status_code >= 400:
                            body = (await response.aread()).decode(
                                "utf-8", errors="ignore"
                            )
                            raise RuntimeError(
                                f"CosyVoice stream failed status={response.status_code} body={body[:200]}"
                            )

                        chunk_count = 0
                        first_chunk_at: float | None = None
                        pending_byte = b""
                        async for chunk in response.aiter_bytes():
                            if not chunk:
                                continue

                            if pending_byte:
                                chunk = pending_byte + chunk
                                pending_byte = b""

                            if len(chunk) % 2 != 0:
                                pending_byte = chunk[-1:]
                                chunk = chunk[:-1]

                            if not chunk:
                                continue

                            chunk_count += 1
                            yielded_any = True
                            if first_chunk_at is None:
                                first_chunk_at = time.perf_counter()
                                logger.info(
                                    "CosyVoice first chunk latency text_len=%s latency=%.3fs",
                                    len(sentence),
                                    first_chunk_at - stream_start,
                                )
                            yield chunk

                        if pending_byte:
                            logger.warning(
                                "CosyVoice stream ended with odd trailing byte; dropping for PCM alignment text_len=%s",
                                len(sentence),
                            )

                        if chunk_count == 0:
                            raise RuntimeError("CosyVoice stream returned no chunks")
                        logger.info(
                            "CosyVoice stream completed text_len=%s chunks=%s total=%.3fs",
                            len(sentence),
                            chunk_count,
                            time.perf_counter() - stream_start,
                        )
                        return
            except Exception as exc:
                if yielded_any:
                    logger.warning(
                        "CosyVoice stream ended early endpoint=%s text_len=%s error=%s",
                        endpoint,
                        len(sentence),
                        exc,
                    )
                    return

                if attempt >= attempts:
                    logger.exception(
                        "CosyVoice stream failed endpoint=%s text_len=%s error=%s",
                        endpoint,
                        len(sentence),
                        exc,
                    )
                    raise RuntimeError("cosyvoice_stream_failed") from exc

                await asyncio.sleep(0.2 * attempt)

    async def _warm_if_needed(self) -> None:
        now = time.perf_counter()
        if now < self._warmed_recently_until:
            return

        async with self._warm_lock:
            now = time.perf_counter()
            if now < self._warmed_recently_until:
                return

            endpoint = f"{self._base_url}{self._tts_path}"
            payload = {
                "tts_text": "嗯。",
                "spk_id": settings.COSYVOICE_VOICE,
                "seed": self._fixed_seed,
                "speed": self._speed,
                **self._extra_payload,
            }
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(8.0, connect=2.0)
                ) as client:
                    async with client.stream(
                        "POST", endpoint, data=payload
                    ) as response:
                        if response.status_code < 400:
                            async for chunk in response.aiter_bytes():
                                if chunk:
                                    break
                self._warmed_recently_until = time.perf_counter() + 25.0
            except Exception:
                self._warmed_recently_until = time.perf_counter() + 5.0

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
            logger.warning("COSYVOICE_EXTRA_PAYLOAD is invalid JSON, ignored")
            return {}
        if not isinstance(value, dict):
            logger.warning("COSYVOICE_EXTRA_PAYLOAD is not JSON object, ignored")
            return {}
        return value

    def _cache_key(self, text: str) -> str:
        raw = (
            f"{settings.TTS_BACKEND}|{settings.COSYVOICE_BASE_URL}|"
            f"{settings.COSYVOICE_TTS_PATH}|{settings.COSYVOICE_VOICE}|"
            f"{settings.COSYVOICE_SAMPLE_RATE}|{settings.COSYVOICE_SPEED}|"
            f"{settings.COSYVOICE_SEED}|{text}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def pcm_chunk_to_wav(self, pcm_bytes: bytes) -> bytes:
        if not pcm_bytes:
            return b""
        if (
            len(pcm_bytes) >= 12
            and pcm_bytes[:4] == b"RIFF"
            and pcm_bytes[8:12] == b"WAVE"
        ):
            return pcm_bytes
        return self._pcm_to_wav(pcm_bytes, settings.COSYVOICE_SAMPLE_RATE)

    def _pcm_to_wav(self, pcm_bytes: bytes, sample_rate: int) -> bytes:
        if len(pcm_bytes) % 2 != 0:
            logger.warning(
                "PCM byte length is odd (%s), dropping trailing byte before WAV wrap",
                len(pcm_bytes),
            )
            pcm_bytes = pcm_bytes[:-1]

        if not pcm_bytes:
            return b""

        output = BytesIO()
        with wave.open(output, "wb") as dst:
            dst.setnchannels(1)
            dst.setsampwidth(2)
            dst.setframerate(sample_rate)
            dst.writeframes(pcm_bytes)
        return output.getvalue()


tts_service = TTSService()

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Optional

from TTS.api import TTS

from app.config import settings

logger = logging.getLogger(__name__)

_TTS_CACHE_SCHEMA = "v1"
_CHUNK_SIZE = 4096


class CoquiXTTSService:
    """CUDA-accelerated Coqui XTTS TTS service."""

    def __init__(
        self,
        model_path: str | None = None,
        device: str = "cuda",
        output_sample_rate: int = 24000,
    ) -> None:
        self._model_path = model_path
        self._device = device
        self._output_sample_rate = output_sample_rate
        self._cache_dir = Path(settings.TTS_CACHE_DIR)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._tts: TTS | None = None
        self._model_loaded = False
        self._load_lock = asyncio.Lock()

    async def ensure_ready(self) -> bool:
        """Load the XTTS model if not already loaded. Returns True if ready."""
        if self._model_loaded and self._tts is not None:
            return True

        async with self._load_lock:
            if self._model_loaded and self._tts is not None:
                return True

            try:
                logger.info(
                    "Loading Coqui XTTS model on device=%s model_path=%s",
                    self._device,
                    self._model_path,
                )

                # Run model loading in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self._tts = await loop.run_in_executor(
                    None,
                    self._init_tts,
                )

                if self._tts is not None:
                    self._model_loaded = True
                    logger.info("Coqui XTTS model loaded successfully")
                    return True

                return False
            except Exception as exc:
                logger.error("Failed to load Coqui XTTS model: %s", exc)
                return False

    def _init_tts(self) -> TTS:
        """Initialize TTS in the executor thread."""
        if self._model_path:
            return TTS(
                model_name=self._model_path,
                gpu=True if self._device == "cuda" else False,
            )
        # Use default XTTS model
        return TTS(
            model_name="xtts",
            gpu=True if self._device == "cuda" else False,
        )

    async def stream_synthesize(self, text: str) -> AsyncIterator[bytes]:
        """
        Synthesize speech and yield PCM audio chunks asynchronously.

        Args:
            text: Input text to synthesize (Chinese)

        Yields:
            PCM audio chunks as bytes
        """
        if not text or not text.strip():
            return

        sentence = text.strip()
        cache_key = self._cache_key(sentence)
        cache_path = self._cache_dir / f"{cache_key}.pcm"

        # Check cache first
        if cache_path.exists():
            logger.debug("TTS cache hit for text length=%s", len(sentence))
            async for chunk in self._read_cached_pcm(cache_path):
                yield chunk
            return

        # Ensure model is ready
        if not await self.ensure_ready():
            raise RuntimeError("Coqui XTTS model not ready")

        # Generate audio
        loop = asyncio.get_event_loop()
        pcm_data = await loop.run_in_executor(
            None,
            self._synthesize_pcm,
            sentence,
        )

        if not pcm_data:
            raise RuntimeError("Coqui XTTS returned empty audio")

        # Cache the result
        try:
            cache_path.write_bytes(pcm_data)
        except Exception as exc:
            logger.warning("Failed to cache TTS output: %s", exc)

        # Yield chunks
        for i in range(0, len(pcm_data), _CHUNK_SIZE):
            yield pcm_data[i : i + _CHUNK_SIZE]

    async def synthesize(self, text: str) -> tuple[bytes, str]:
        """
        Synthesize speech and return complete PCM audio.

        Args:
            text: Input text to synthesize (Chinese)

        Returns:
            Tuple of (PCM bytes, format string)
        """
        if not text or not text.strip():
            return b"", "pcm"

        chunks: list[bytes] = []
        async for chunk in self.stream_synthesize(text):
            chunks.append(chunk)

        if not chunks:
            return b"", "pcm"

        pcm_bytes = b"".join(chunks)
        return pcm_bytes, "pcm"

    def _synthesize_pcm(self, text: str) -> bytes:
        """
        Synthesize speech and return raw PCM bytes (runs in executor).

        Args:
            text: Input text to synthesize

        Returns:
            Raw PCM audio bytes
        """
        if self._tts is None:
            raise RuntimeError("TTS model not initialized")

        # Generate wav using xtts method with language
        # TTS outputs 24kHz mono by default for xtts
        wav = self._tts.tts(
            text=text,
            language="zh",
        )

        if wav is None or len(wav) == 0:
            return b""

        # Convert numpy array to PCM bytes
        import numpy as np

        wav_array = np.array(wav, dtype=np.float32)

        # Normalize to 16-bit PCM
        wav_array = np.clip(wav_array, -1.0, 1.0)
        pcm_int16 = (wav_array * 32767).astype(np.int16)

        return pcm_int16.tobytes()

    async def _read_cached_pcm(self, cache_path: Path) -> AsyncIterator[bytes]:
        """Read cached PCM file and yield chunks."""
        try:
            pcm_data = cache_path.read_bytes()
            for i in range(0, len(pcm_data), _CHUNK_SIZE):
                yield pcm_data[i : i + _CHUNK_SIZE]
        except Exception as exc:
            logger.warning("Failed to read PCM cache: %s", exc)

    def _cache_key(self, text: str) -> str:
        """Generate a cache key for the given text."""
        raw = f"{_TTS_CACHE_SCHEMA}|xtts|{self._device}|{self._output_sample_rate}|{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @property
    def is_ready(self) -> bool:
        """Check if the model is loaded and ready."""
        return self._model_loaded and self._tts is not None

    @property
    def sample_rate(self) -> int:
        """Get the output sample rate."""
        return self._output_sample_rate


# Module-level singleton instance
coqui_xtts_service = CoquiXTTSService()
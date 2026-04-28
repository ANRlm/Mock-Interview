from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from app.services.audio_utils import resample_pcm_s16le as _resample_pcm_s16le

logger = logging.getLogger(__name__)

_TARGET_SAMPLE_RATE = 16000

# faster_whisper imports - handle case where it's not installed
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None  # type: ignore


class FasterWhisperSTTService:
    """CUDA-accelerated Faster-Whisper STT service.

    This is a local inference service - no HTTP server required.
    Model auto-downloads to ~/.cache/whisper.

    Args:
        model_size: Whisper model size (default: "large-v3")
        device: Device for inference (default: "cuda")
        compute_type: Computation type (default: "float16")
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
    ) -> None:
        if WhisperModel is None:
            raise RuntimeError(
                "faster-whisper is not installed. "
                "Add 'faster-whisper' to requirements.txt"
            )

        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model: Any = None

    async def ensure_model_ready(self) -> bool:
        """Load the Whisper model (async wrapper for blocking load)."""
        if self._model is not None:
            return True

        try:
            import asyncio

            def _load() -> None:
                logger.info(
                    "Loading Faster-Whisper model: size=%s device=%s compute_type=%s",
                    self._model_size,
                    self._device,
                    self._compute_type,
                )
                self._model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                    download_root=os.path.expanduser("~/.cache/whisper"),
                )
                logger.info("Faster-Whisper model loaded successfully")

            await asyncio.to_thread(_load)
            return True
        except Exception as exc:
            logger.exception("Failed to load Faster-Whisper model: %s", exc)
            return False

    async def transcribe_streaming(
        self,
        pcm_bytes: bytes,
        sample_rate: int = _TARGET_SAMPLE_RATE,
    ) -> tuple[list[str], str]:
        """Transcribe audio and return (partials, final_text)."""
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
        """Transcribe audio stream, yielding (event_type, text) tuples.

        Yields:
            ("partial", text) for intermediate results
            ("final", text) for the final transcription
        """
        if not pcm_bytes:
            return

        # Ensure model is loaded
        if self._model is None:
            ready = await self.ensure_model_ready()
            if not ready:
                raise RuntimeError("faster_whisper_model_not_ready")

        # Normalize PCM16 mono to target sample rate
        normalized_pcm = self._normalize_pcm16_mono(
            pcm_bytes=pcm_bytes,
            source_rate=sample_rate,
            target_rate=_TARGET_SAMPLE_RATE,
        )
        if not normalized_pcm:
            return

        # Convert PCM16 bytes to float32 numpy array
        audio_float32 = self._pcm16_to_float32(normalized_pcm)

        try:
            import asyncio

            # Run transcription in thread to avoid blocking
            def _transcribe() -> dict[str, Any]:
                segments, info = self._model.transcribe(
                    audio_float32,
                    language="zh",
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    initial_prompt=None,
                )

                result = {"segments": list(segments), "language": info.language}
                return result

            result = await asyncio.to_thread(_transcribe)

            has_partial = False
            for segment in result["segments"]:
                text = segment.text.strip()
                if not text:
                    continue

                # Check if this is a final segment
                if hasattr(segment, "words") and segment.words:
                    # For segments with word-level timestamps, yield as partial first
                    if not has_partial:
                        yield ("partial", text)
                        has_partial = True
                else:
                    yield ("final", text)
                    return

            # If we yielded partials but no final, use the last partial as final
            if has_partial:
                logger.debug("Using last partial as final text")

        except Exception as exc:
            logger.exception(
                "Faster-Whisper transcription failed: source_rate=%s bytes=%s error=%s",
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
        """Normalize PCM16 mono to target sample rate."""
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

    def _pcm16_to_float32(self, pcm_bytes: bytes) -> Any:
        """Convert PCM16 bytes to float32 numpy array in range [-1, 1]."""
        import array
        import numpy as np

        # Convert bytes to signed 16-bit integers
        pcm_int16 = array.array("h", pcm_bytes)
        # Convert to float32 and normalize to [-1, 1]
        audio_float32 = np.array(pcm_int16, dtype=np.float32) / 32768.0
        return audio_float32

    def _build_partials(self, online_texts: list[str], final_text: str) -> list[str]:
        """Build cleaned list of partial transcriptions."""
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


faster_whisper_stt_service = FasterWhisperSTTService()

import asyncio
import struct
from typing import NamedTuple


class VADEvent(NamedTuple):
    speech_detected: bool
    confidence: float
    timestamp: float


class VADService:
    def __init__(self):
        self._model = None  # Lazy load
        self._sample_rate = 16000

    async def detect_speech(self, pcm_chunk: bytes) -> VADEvent:
        # Energy-based detection as fallback when Silero unavailable
        samples = len(pcm_chunk) // 2
        if samples == 0:
            return VADEvent(speech_detected=False, confidence=0.0, timestamp=0.0)

        values = struct.unpack(f'<{samples}h', pcm_chunk)
        energy = sum(abs(v) for v in values) / samples

        # Energy threshold
        threshold = 500
        speech = energy > threshold
        confidence = min(energy / threshold, 1.0) if speech else energy / threshold
        return VADEvent(speech_detected=speech, confidence=confidence, timestamp=0.0)

    async def detect_turn_end(self, pcm_chunks: list[bytes]) -> bool:
        # Detect silence across multiple chunks
        silence_count = 0
        for chunk in pcm_chunks:
            event = await self.detect_speech(chunk)
            if not event.speech_detected:
                silence_count += 1
            else:
                silence_count = 0
        return silence_count >= 3  # 3+ consecutive silence chunks = turn end


vad_service = VADService()
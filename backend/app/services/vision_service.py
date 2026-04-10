from __future__ import annotations

import asyncio
import base64
from collections import Counter


class VisionService:
    async def analyze_frame(self, image_base64: str | None) -> tuple[str, float]:
        if not image_base64:
            return ("neutral", 0.5)

        try:
            await asyncio.to_thread(base64.b64decode, image_base64.encode("utf-8"))
            return ("neutral", 0.72)
        except Exception:
            return ("neutral", 0.4)

    def summarize(
        self, emotions: list[str], eye_scores: list[float]
    ) -> tuple[str, float, float]:
        emotion_counter = Counter(emotions)
        dominant_emotion = (
            emotion_counter.most_common(1)[0][0] if emotions else "neutral"
        )
        avg_eye_contact = sum(eye_scores) / len(eye_scores) if eye_scores else 0.0
        behavior_score = min(100.0, max(0.0, avg_eye_contact * 100 * 0.85 + 15))
        return dominant_emotion, avg_eye_contact, behavior_score


vision_service = VisionService()

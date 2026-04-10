from __future__ import annotations

import asyncio
import base64
from collections import Counter
from dataclasses import dataclass
from statistics import mean


@dataclass(slots=True)
class BehaviorSummary:
    dominant_emotion: str
    avg_eye_contact: float
    behavior_score: float
    attention_score: float
    posture_score: float
    engagement_score: float
    gaze_stability: float
    emotion_confidence: float
    recommendations: list[str]


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
        self,
        *,
        emotions: list[str],
        emotion_confidences: list[float],
        eye_scores: list[float],
        head_pose_scores: list[float],
        gaze_x_values: list[float],
        gaze_y_values: list[float],
    ) -> BehaviorSummary:
        emotion_counter = Counter(emotions)
        dominant_emotion = (
            emotion_counter.most_common(1)[0][0] if emotions else "neutral"
        )

        avg_eye_contact = self._safe_mean(eye_scores)
        avg_head_pose = self._safe_mean(head_pose_scores)
        avg_emotion_conf = self._safe_mean(emotion_confidences)

        gaze_stability = self._gaze_stability(gaze_x_values, gaze_y_values)
        attention_score = self._clamp01(avg_eye_contact * 0.55 + gaze_stability * 0.45)
        posture_score = self._clamp01(avg_head_pose)
        engagement_score = self._clamp01(
            avg_emotion_conf * 0.35 + attention_score * 0.35 + posture_score * 0.30
        )

        behavior_score = round(
            self._clamp01(
                attention_score * 0.45 + posture_score * 0.35 + engagement_score * 0.20
            )
            * 100,
            2,
        )

        recommendations = self._build_recommendations(
            attention_score=attention_score,
            posture_score=posture_score,
            engagement_score=engagement_score,
            dominant_emotion=dominant_emotion,
        )

        return BehaviorSummary(
            dominant_emotion=dominant_emotion,
            avg_eye_contact=round(avg_eye_contact, 4),
            behavior_score=behavior_score,
            attention_score=round(attention_score * 100, 2),
            posture_score=round(posture_score * 100, 2),
            engagement_score=round(engagement_score * 100, 2),
            gaze_stability=round(gaze_stability * 100, 2),
            emotion_confidence=round(avg_emotion_conf * 100, 2),
            recommendations=recommendations,
        )

    def _safe_mean(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return float(mean(values))

    def _clamp01(self, value: float) -> float:
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value

    def _gaze_stability(
        self, gaze_x_values: list[float], gaze_y_values: list[float]
    ) -> float:
        if not gaze_x_values and not gaze_y_values:
            return 0.5

        def _score_axis(values: list[float]) -> float:
            if not values:
                return 0.5
            axis_mean = self._safe_mean(values)
            mad = self._safe_mean([abs(v - axis_mean) for v in values])
            return self._clamp01(1.0 - min(1.0, mad * 2.5))

        score_x = _score_axis(gaze_x_values)
        score_y = _score_axis(gaze_y_values)
        return (score_x + score_y) / 2

    def _build_recommendations(
        self,
        *,
        attention_score: float,
        posture_score: float,
        engagement_score: float,
        dominant_emotion: str,
    ) -> list[str]:
        tips: list[str] = []

        if attention_score < 0.55:
            tips.append("建议提升镜头注视时长，减少频繁游离视线，以增强专注感。")
        if posture_score < 0.60:
            tips.append("建议保持头部与肩颈姿态稳定，避免大幅度晃动影响表达可信度。")
        if engagement_score < 0.58:
            tips.append("建议在回答关键点时增加语气与表情变化，提升互动投入感。")
        if dominant_emotion in {"sad", "angry", "fear"}:
            tips.append("建议在面试中保持更积极平稳的面部状态，避免负向情绪持续暴露。")

        if not tips:
            tips.append("整体行为表现稳定，可继续保持当前的镜头交流与姿态控制。")

        return tips


vision_service = VisionService()

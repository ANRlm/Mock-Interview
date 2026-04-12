from __future__ import annotations

import asyncio
import base64
import io
import math
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


# ---------------------------------------------------------------------------
# Emotion analysis utilities
# ---------------------------------------------------------------------------

def _compute_mouth_aspect_ratio(landmarks: list[tuple[float, float]]) -> float | None:
    """Estimate mouth openness from a set of mouth landmarks (relative 0-1).

    Returns a ratio where higher values indicate a more open mouth.
    Returns None if not enough landmarks.
    """
    if len(landmarks) < 6:
        return None
    # Simple vertical vs horizontal ratio heuristic
    try:
        top = min(lm[1] for lm in landmarks[:3])
        bottom = max(lm[1] for lm in landmarks[:3])
        width = abs(landmarks[0][0] - landmarks[3][0]) if len(landmarks) > 3 else 0.001
        height = bottom - top
        return height / max(width, 0.001)
    except Exception:
        return None


def _mouth_corner_slope(landmarks: list[tuple[float, float]]) -> float | None:
    """Estimate smile from mouth corner positions.

    Returns positive for upturned corners (smile), negative for downturned (frown).
    """
    if len(landmarks) < 6:
        return None
    try:
        left = landmarks[0]
        right = landmarks[3]
        center = landmarks[len(landmarks) // 2]
        # Smile: corners higher than center
        left_raise = left[1] - center[1]
        right_raise = right[1] - center[1]
        return -(left_raise + right_raise) / 2  # negative = corners above center
    except Exception:
        return None


def _blink_rate_from_eye_openness(
    eye_openness_history: list[float],
) -> float:
    """Estimate blink rate from recent eye openness values.

    Returns estimated blinks per second.
    """
    if len(eye_openness_history) < 3:
        return 0.5  # default
    diffs = [eye_openness_history[i] - eye_openness_history[i - 1]
             for i in range(1, len(eye_openness_history))]
    blinks = sum(1 for d in diffs if d < -0.15)  # sharp drops indicate blinks
    return blinks / max(len(eye_openness_history) * 0.2, 1)


_EMOTION_KEYS = ("neutral", "happy", "sad", "angry", "fear", "surprise", "disgust")


def _infer_emotion_from_scores(
    eye_contact: float,
    head_pose: float,
    smile_score: float | None,
    mouth_openness: float | None,
    blink_rate: float,
) -> tuple[str, float]:
    """Infer emotion label and confidence from behavioral signals.

    Args:
        eye_contact: 0-1, higher = more engaged
        head_pose: 0-1, higher = more stable/forward
        smile_score: negative=upturned corners (happy), positive=downturned, None=unknown
        mouth_openness: 0-1, higher = more open
        blink_rate: blinks per second

    Returns:
        (emotion_label, confidence)
    """
    engagement = (eye_contact + head_pose) / 2

    # Blink rate norms: humans blink ~15-20 per minute = 0.25-0.33 per second
    blink_norm = max(0.0, min(1.0, blink_rate / 1.0))

    if smile_score is not None and smile_score < -0.02 and engagement > 0.55:
        # Upward mouth corners + good engagement → happy
        conf = min(0.9, 0.5 + abs(smile_score) * 2 + engagement * 0.3)
        return ("happy", conf)

    if mouth_openness is not None and mouth_openness > 0.35 and engagement < 0.4:
        # Wide open mouth + low engagement → surprise/fear
        conf = min(0.85, mouth_openness * 1.5)
        return ("surprise", conf)

    if engagement > 0.65:
        # High engagement, neutral face → calm/positive
        if blink_norm > 0.7:
            return ("fear", 0.55)  # rapid blinking can indicate anxiety
        return ("neutral", 0.5 + engagement * 0.4)

    if engagement < 0.35:
        # Low engagement → sad or fear
        if blink_norm > 0.6:
            return ("fear", 0.65)
        return ("sad", 0.55 + (0.5 - engagement) * 0.4)

    if head_pose < 0.4:
        # Looking away → fear or thinking
        return ("fear", 0.6)

    # Default
    return ("neutral", 0.5)


# ---------------------------------------------------------------------------
# Main VisionService
# ---------------------------------------------------------------------------

class VisionService:
    async def analyze_frame(self, image_base64: str | None) -> tuple[str, float]:
        """Analyze a single video frame for emotion inference.

        Uses basic image processing to extract facial signals (smile, mouth openness)
        combined with behavioral heuristics to classify emotion.

        Returns:
            (emotion_label, confidence)
        """
        if not image_base64:
            return ("neutral", 0.5)

        try:
            image_data = await asyncio.to_thread(
                base64.b64decode, image_base64.encode("utf-8")
            )
        except Exception:
            return ("neutral", 0.4)

        # Use heuristic analysis on the decoded image
        emotion, confidence = await asyncio.to_thread(
            self._analyze_image_heuristic, image_data
        )
        return (emotion, confidence)

    def _analyze_image_heuristic(self, raw_bytes: bytes) -> tuple[str, float]:
        """Perform heuristic facial analysis on raw image bytes.

        Uses PIL to detect basic facial features without ML models.
        Falls back to neutral if image cannot be decoded.
        """
        try:
            import PIL.Image as Image
            import PIL.ImageStat as ImageStat

            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            w, h = img.size

            # Simple region-based color analysis for smile detection
            # Mouth region: lower-center portion of face (heuristic)
            mouth_top = int(h * 0.62)
            mouth_bottom = int(h * 0.78)
            mouth_left = int(w * 0.32)
            mouth_right = int(w * 0.68)
            mouth_region = img.crop((mouth_left, mouth_top, mouth_right, mouth_bottom))

            mouth_stats = ImageStat.Stat(mouth_region)
            mouth_r, mouth_g, mouth_b = mouth_stats.mean[:3]

            # Mouth redness and color: more red → more active (speaking/smiling)
            mouth_redness = (mouth_r - (mouth_g + mouth_b) / 2) / max(mouth_r, 1)
            mouth_openness_estimate = max(0.0, min(1.0, mouth_redness * 2 + 0.2))

            # Eye region analysis for brightness (proxy for eye openness)
            eye_top = int(h * 0.28)
            eye_bottom = int(h * 0.45)
            eye_left = int(w * 0.25)
            eye_right = int(w * 0.75)
            eye_region = img.crop((eye_left, eye_top, eye_right, eye_bottom))
            eye_stats = ImageStat.Stat(eye_region)
            eye_brightness = sum(eye_stats.mean[:3]) / 3

            # Smile heuristic: mouth corners higher (lower y) = smile
            # Use color differential between upper and lower lip area
            upper_lip_top = int(h * 0.63)
            upper_lip_bottom = int(h * 0.66)
            upper_lip_region = img.crop((mouth_left, upper_lip_top, mouth_right, upper_lip_bottom))
            lower_lip_top = int(h * 0.70)
            lower_lip_bottom = int(h * 0.74)
            lower_lip_region = img.crop((mouth_left, lower_lip_top, mouth_right, lower_lip_bottom))

            upper_stats = ImageStat.Stat(upper_lip_region)
            lower_stats = ImageStat.Stat(lower_lip_region)
            upper_r = upper_stats.mean[0]
            lower_r = lower_stats.mean[0]

            # Corner smile heuristic
            left_corner_area = img.crop((int(w * 0.30), int(h * 0.64), int(w * 0.40), int(h * 0.70)))
            right_corner_area = img.crop((int(w * 0.60), int(h * 0.64), int(w * 0.70), int(h * 0.70)))
            left_stats = ImageStat.Stat(left_corner_area)
            right_stats = ImageStat.Stat(right_corner_area)

            left_brightness = sum(left_stats.mean[:3]) / 3
            right_brightness = sum(right_stats.mean[:3]) / 3
            corner_diff = abs(left_brightness - right_brightness)

            # Higher corner brightness relative to center → upturned corners (smile)
            smile_score = (corner_diff - 10) / 30.0  # normalize

            # Blink rate proxy: brightness variation in eye region
            eye_variance = sum(eye_stats.stddev[:3]) / 3
            blink_rate_estimate = min(1.0, eye_variance / 30.0)

            # Use heuristic inference
            emotion, conf = _infer_emotion_from_scores(
                eye_contact=0.5,  # Will be overridden by MediaPipe data in real flow
                head_pose=0.5,    # Will be overridden by MediaPipe data in real flow
                smile_score=smile_score,
                mouth_openness=mouth_openness_estimate,
                blink_rate=blink_rate_estimate,
            )
            return (emotion, conf)

        except Exception:
            return ("neutral", 0.5)

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

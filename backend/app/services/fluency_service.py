from __future__ import annotations


def analyze_fluency(transcript: str) -> dict[str, float | dict[str, float]]:
    filler_words = ["嗯", "啊", "那个", "就是", "然后"]
    total_chars = max(len(transcript.replace(" ", "")), 1)
    filler_hits = sum(transcript.count(word) for word in filler_words)
    filler_ratio = min(filler_hits / total_chars, 1.0)

    estimated_minutes = max(total_chars / 180, 0.5)
    speech_rate = total_chars / estimated_minutes
    pause_frequency = (
        max(transcript.count("，") + transcript.count("。") - 2, 0) / estimated_minutes
    )

    score = (
        100
        - filler_ratio * 40
        - min(abs(speech_rate - 180), 120) / 120 * 30
        - min(pause_frequency, 20) / 20 * 30
    )
    score = max(0.0, min(100.0, score))

    return {
        "fluency_score": round(score, 2),
        "speech_rate_wpm": round(speech_rate, 2),
        "filler_word_ratio": round(filler_ratio, 4),
        "pause_frequency": round(pause_frequency, 2),
        "detail": {
            "char_count": float(total_chars),
            "filler_count": float(filler_hits),
        },
    }

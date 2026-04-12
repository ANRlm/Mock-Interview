from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any


class TTSMetricsService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rows: deque[dict[str, Any]] = deque(maxlen=2000)

    def record(self, row: dict[str, Any]) -> None:
        enriched = dict(row)
        enriched.setdefault("ts", time.time())
        with self._lock:
            self._rows.append(enriched)

    def clear(self) -> None:
        with self._lock:
            self._rows.clear()

    def summary(self) -> dict[str, Any]:
        with self._lock:
            rows = list(self._rows)

        if not rows:
            return {
                "count": 0,
                "session_count": 0,
                "first_audio": {},
                "provider_first_chunk": {},
                "attempts": {},
                "hedge": {},
                "latency_buckets": {
                    "lt_2s": 0,
                    "2_to_3s": 0,
                    "gte_3s": 0,
                },
                "recent": [],
            }

        def collect(rows_src: list[dict[str, Any]], key: str) -> list[float]:
            vals: list[float] = []
            for item in rows_src:
                value = item.get(key)
                if isinstance(value, (int, float)):
                    vals.append(float(value))
            return vals

        session_rows = [item for item in rows if "session_id" in item]
        session_success_rows = [
            item for item in session_rows if item.get("tts_success")
        ]
        provider_rows = [item for item in rows if item.get("source") == "provider"]

        def stats(values: list[float]) -> dict[str, float]:
            if not values:
                return {}
            sv = sorted(values)
            n = len(sv)
            p50 = sv[n // 2] if n % 2 else (sv[n // 2 - 1] + sv[n // 2]) / 2
            p90 = sv[min(n - 1, max(0, int(n * 0.9) - 1))]
            p99 = sv[min(n - 1, max(0, int(n * 0.99) - 1))]
            return {
                "min": round(sv[0], 3),
                "p50": round(p50, 3),
                "p90": round(p90, 3),
                "p99": round(p99, 3),
                "max": round(sv[-1], 3),
            }

        attempts_vals = collect(provider_rows, "attempt_count")
        attempts_avg = (
            round(sum(attempts_vals) / len(attempts_vals), 3) if attempts_vals else 0.0
        )

        buckets = {
            "lt_2s": 0,
            "2_to_3s": 0,
            "gte_3s": 0,
        }
        for item in session_rows:
            latency = item.get("tts_first_audio_seconds")
            if not isinstance(latency, (int, float)):
                continue
            v = float(latency)
            if v < 2.0:
                buckets["lt_2s"] += 1
            elif v < 3.0:
                buckets["2_to_3s"] += 1
            else:
                buckets["gte_3s"] += 1

        hedge_rows = [item for item in provider_rows if item.get("hedge_enabled")]
        hedge_triggered_vals = collect(hedge_rows, "hedge_triggered_segments")
        hedge_max_racers_vals = collect(hedge_rows, "hedge_max_racers")
        hedge_runs = len(hedge_rows)
        hedge_triggered_runs = len([v for v in hedge_triggered_vals if v > 0])
        hedge_triggered_total_segments = int(sum(hedge_triggered_vals))
        hedge_triggered_rate = (
            round(hedge_triggered_runs / hedge_runs, 3) if hedge_runs else 0.0
        )
        hedge_avg_max_racers = (
            round(sum(hedge_max_racers_vals) / len(hedge_max_racers_vals), 3)
            if hedge_max_racers_vals
            else 0.0
        )
        success_count = len(session_success_rows)
        success_rate = (
            round(success_count / len(session_rows), 3) if session_rows else 0.0
        )

        return {
            "count": len(rows),
            "session_count": len(session_rows),
            "session_success": {
                "count": success_count,
                "rate": success_rate,
            },
            "first_audio": stats(collect(session_rows, "tts_first_audio_seconds")),
            "provider_first_chunk": stats(
                collect(provider_rows, "provider_first_chunk_seconds")
            ),
            "attempts": {
                "avg": attempts_avg,
                "max": max(attempts_vals) if attempts_vals else 0,
            },
            "hedge": {
                "runs": hedge_runs,
                "triggered_runs": hedge_triggered_runs,
                "triggered_rate": hedge_triggered_rate,
                "triggered_segments_total": hedge_triggered_total_segments,
                "avg_max_racers": hedge_avg_max_racers,
                "max_racers": max(hedge_max_racers_vals)
                if hedge_max_racers_vals
                else 0,
            },
            "latency_buckets": buckets,
            "recent": rows[-20:],
        }

    def dump(self, path: str | Path) -> None:
        payload = self.summary()
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )


tts_metrics_service = TTSMetricsService()

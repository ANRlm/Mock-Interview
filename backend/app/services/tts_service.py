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
from contextlib import suppress
from dataclasses import dataclass

import httpx

from app.config import settings
from app.services.tts_metrics_service import tts_metrics_service
from app.services.tts_text_service import tts_text_normalizer


TTS_PROVIDER_COSYVOICE2 = "cosyvoice2-http"


logger = logging.getLogger(__name__)

_EN_LETTER_RE = re.compile(r"[A-Za-z]")
_END_PUNCT_RE = re.compile(r"[。！？!?；;]")
_EN_PHONETIC_RE = re.compile(
    r"诶|比|西|迪|伊|艾弗|吉|艾尺|艾|杰|开|艾勒|艾姆|艾恩|欧|屁|丘|阿尔|艾丝|提|优|维|达布流|艾克斯|外|贼德"
)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_TTS_CACHE_SCHEMA = "v13"


def _has_english(text: str) -> bool:
    return bool(_EN_LETTER_RE.search(text or ""))


@dataclass
class _RaceCandidate:
    idx: int
    queue: asyncio.Queue[bytes | None]
    task: asyncio.Task[None] | None = None
    error: Exception | None = None


class TTSService:
    _keep_warm_task: asyncio.Task | None = None
    _last_keep_warm_at: float = 0.0

    def __init__(self) -> None:
        self._cache_dir = Path(settings.TTS_CACHE_DIR)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._base_url = settings.COSYVOICE_BASE_URL.rstrip("/")
        self._tts_path = self._normalize_path(settings.COSYVOICE_TTS_PATH)
        self._health_path = self._normalize_path(settings.COSYVOICE_HEALTH_PATH)
        self._mode = (settings.COSYVOICE_MODE or "sft").strip().lower()
        if self._mode not in {"sft", "instruct"}:
            self._mode = "sft"
        self._instruct_text = (settings.COSYVOICE_INSTRUCT_TEXT or "").strip()
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
        self._instruct_unavailable_until = 0.0
        self._instruct_backoff_seconds = 21_600.0
        self._warm_timeout_seconds = max(
            0.1, float(getattr(settings, "COSYVOICE_WARM_TIMEOUT_SECONDS", 0.8))
        )
        self._warm_keepalive_seconds = max(
            10.0,
            float(getattr(settings, "COSYVOICE_WARM_KEEPALIVE_SECONDS", 90.0)),
        )
        self._request_timeout_seconds = max(
            5.0, float(getattr(settings, "TTS_REQUEST_TIMEOUT_SECONDS", 20.0))
        )
        self._first_chunk_timeout_seconds = min(
            self._request_timeout_seconds,
            max(
                0.8,
                float(getattr(settings, "TTS_FIRST_CHUNK_TIMEOUT_SECONDS", 6.5)),
            ),
        )
        self._hedge_enabled = bool(getattr(settings, "TTS_HEDGE_ENABLED", False))
        self._hedge_delay_seconds = max(
            0.05, float(getattr(settings, "TTS_HEDGE_DELAY_SECONDS", 0.3))
        )
        self._hedge_max_racers = max(
            1, int(getattr(settings, "TTS_HEDGE_MAX_RACERS", 2))
        )
        self._last_attempt_count = 0
        self._last_hedge_racers = 0

    async def ensure_ready(self) -> bool:
        if settings.TTS_BACKEND != TTS_PROVIDER_COSYVOICE2:
            logger.warning("Unsupported TTS backend: %s", settings.TTS_BACKEND)
            return False

        active_mode = self._active_mode()
        endpoint = self._resolve_endpoint(active_mode)
        probe_payload = self._build_payload_for_mode("你好。", active_mode)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                health = await client.get(f"{self._base_url}{self._health_path}")
                if health.status_code >= 400:
                    logger.warning(
                        "CosyVoice health check failed: status=%s body=%s",
                        health.status_code,
                        health.text[:200],
                    )

                if await self._probe_stream_chunk(client, endpoint, probe_payload):
                    self._warmed_recently_until = time.perf_counter() + 300.0
                    return True

                if active_mode == "instruct":
                    self._mark_instruct_unavailable()
                    fallback_endpoint = self._resolve_endpoint("sft")
                    fallback_payload = self._build_payload_for_mode("你好。", "sft")
                    fallback_ok = await self._probe_stream_chunk(
                        client,
                        fallback_endpoint,
                        fallback_payload,
                    )
                    if fallback_ok:
                        self._warmed_recently_until = time.perf_counter() + 300.0
                    return fallback_ok
                return False
        except Exception as exc:
            logger.warning(
                "CosyVoice health/probe error endpoint=%s error=%s", endpoint, exc
            )
            return False

    async def warmup_if_needed(self) -> None:
        await self._warm_if_needed()
        # Start background keep-warm task
        self._start_keep_warm()

    def _start_keep_warm(self) -> None:
        """Start background task to keep TTS warm."""
        if TTSService._keep_warm_task and not TTSService._keep_warm_task.done():
            return
        TTSService._keep_warm_task = asyncio.create_task(self._keep_warm_loop())

    async def _keep_warm_loop(self) -> None:
        """Periodically send warmup requests to keep CosyVoice hot."""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                if time.perf_counter() - self._last_keep_warm_at > 25:
                    await self._do_keep_warm()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _do_keep_warm(self) -> None:
        """Send a minimal warmup request."""
        try:
            endpoint = self._resolve_endpoint(self._active_mode())
            payload = self._build_payload_for_mode("好", self._active_mode())
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                async with client.stream("POST", endpoint, data=payload) as resp:
                    async for _ in resp.aiter_bytes():
                        break
            self._last_keep_warm_at = time.perf_counter()
        except Exception:
            pass

    def prepare_text_for_tts(self, text: str, *, fallback: str = "请继续。") -> str:
        return tts_text_normalizer.normalize(text, fallback=fallback)

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
        stream_start = time.perf_counter()
        provider_first_chunk_seconds: float | None = None
        attempt_count = 0
        hedge_triggered_segments = 0
        hedge_max_racers = 0
        cache_key = self._cache_key(sentence)
        wav_cache_path = self._cache_dir / f"{cache_key}.wav"
        if wav_cache_path.exists():
            logger.debug("TTS stream cache hit (wav) for text length=%s", len(sentence))
            cached_pcm = self._wav_to_pcm_if_needed(wav_cache_path.read_bytes())
            if cached_pcm:
                yield cached_pcm
            tts_metrics_service.record(
                {
                    "source": "cache",
                    "text_len": len(sentence),
                    "attempt_count": 0,
                    "provider_first_chunk_seconds": 0.0,
                }
            )
            return

        chunks = self._split_for_quality(sentence)
        for part_idx, part in enumerate(chunks):
            async for chunk in self._stream_sentence(
                part,
                is_first_segment=(part_idx == 0),
            ):
                attempt_count = max(
                    attempt_count, int(getattr(self, "_last_attempt_count", 0))
                )
                if provider_first_chunk_seconds is None:
                    provider_first_chunk_seconds = time.perf_counter() - stream_start
                yield chunk
            hedge_racers = int(getattr(self, "_last_hedge_racers", 0))
            hedge_max_racers = max(hedge_max_racers, hedge_racers)
            if hedge_racers > 1:
                hedge_triggered_segments += 1

        tts_metrics_service.record(
            {
                "source": "provider",
                "text_len": len(sentence),
                "segment_count": len(chunks),
                "attempt_count": attempt_count,
                "provider_first_chunk_seconds": provider_first_chunk_seconds,
                "hedge_enabled": self._hedge_enabled,
                "hedge_triggered_segments": hedge_triggered_segments,
                "hedge_max_racers": hedge_max_racers,
            }
        )

    async def _stream_sentence(
        self,
        sentence: str,
        *,
        is_first_segment: bool = False,
    ) -> AsyncIterator[bytes]:
        self._last_attempt_count = 0
        self._last_hedge_racers = 0
        await self._warm_if_needed()
        active_mode = self._active_mode()
        primary_endpoint = self._resolve_endpoint(active_mode)
        primary_payload = self._build_payload_for_mode(sentence, active_mode)

        # Simplified: only use primary candidate for speed
        attempt_candidates: list[tuple[str, dict[str, object]]] = [
            (primary_endpoint, primary_payload)
        ]

        # Only add fallback if instruct mode
        if active_mode == "instruct":
            fallback_endpoint = self._resolve_endpoint("sft")
            fallback_payload = self._build_payload_for_mode(sentence, "sft")
            attempt_candidates.append((fallback_endpoint, fallback_payload))

        if self._should_enable_hedge(
            sentence,
            attempt_candidates,
            is_first_segment=is_first_segment,
        ):
            hedge_delay_seconds = self._resolve_hedge_delay_for_text(sentence)
            hedged_emitted = False
            try:
                async for chunk in self._stream_sentence_with_hedge(
                    attempt_candidates=attempt_candidates,
                    hedge_delay_seconds=hedge_delay_seconds,
                    text_len=len(sentence),
                ):
                    hedged_emitted = True
                    yield chunk
                return
            except Exception as exc:
                if hedged_emitted:
                    logger.warning(
                        "TTS hedge ended early endpoint=%s text_len=%s error=%s",
                        primary_endpoint,
                        len(sentence),
                        exc,
                    )
                    return
                logger.warning(
                    "TTS hedge race failed, fallback to sequential endpoint=%s text_len=%s error=%s",
                    primary_endpoint,
                    len(sentence),
                    exc,
                )

        last_error: Exception | None = None
        first_chunk_timeout = (
            self._first_chunk_timeout_seconds
            if is_first_segment
            else self._request_timeout_seconds
        )
        for idx, (endpoint, payload) in enumerate(attempt_candidates, start=1):
            self._last_attempt_count = idx
            queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=128)
            stream_error: Exception | None = None

            async def producer() -> None:
                nonlocal stream_error
                try:
                    async for pcm in self._stream_with_retries(
                        endpoint=endpoint,
                        payload=payload,
                        text_len=len(sentence),
                    ):
                        await queue.put(pcm)
                except Exception as exc:  # noqa: PERF203
                    stream_error = exc
                finally:
                    await queue.put(None)

            producer_task = asyncio.create_task(producer())
            produced_any = False

            try:
                while True:
                    timeout_seconds = (
                        first_chunk_timeout
                        if not produced_any
                        else self._request_timeout_seconds
                    )
                    try:
                        item = await asyncio.wait_for(
                            queue.get(), timeout=timeout_seconds
                        )
                    except asyncio.TimeoutError as exc:
                        timeout_kind = (
                            "tts_first_chunk_timeout"
                            if not produced_any
                            else "tts_sentence_timeout"
                        )
                        stream_error = RuntimeError(
                            f"{timeout_kind} len={len(sentence)} timeout={timeout_seconds}s"
                        )
                        raise stream_error from exc

                    if item is None:
                        break

                    produced_any = True
                    yield item
            except Exception as exc:
                last_error = exc
                producer_task.cancel()
                with suppress(asyncio.CancelledError):
                    await producer_task
                continue

            await producer_task
            if produced_any:
                return

            if stream_error is not None:
                last_error = stream_error

        if active_mode == "instruct":
            self._mark_instruct_unavailable()
            fallback_endpoint = self._resolve_endpoint("sft")
            fallback_payload = self._build_payload_for_mode(sentence, "sft")
            async for chunk in self._stream_with_retries(
                endpoint=fallback_endpoint,
                payload=fallback_payload,
                text_len=len(sentence),
            ):
                yield chunk
            return

        if last_error is not None:
            raise last_error

    async def _stream_sentence_with_hedge(
        self,
        *,
        attempt_candidates: list[tuple[str, dict[str, object]]],
        hedge_delay_seconds: float,
        text_len: int,
    ) -> AsyncIterator[bytes]:
        max_racers = max(1, min(self._hedge_max_racers, len(attempt_candidates)))
        last_error: Exception | None = None
        yielded_any = False
        active: list[_RaceCandidate] = []
        next_idx = 0
        next_launch_at = 0.0
        launched_count = 0

        async def _start_candidate(idx: int) -> _RaceCandidate:
            queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=128)
            candidate = _RaceCandidate(idx=idx, queue=queue)
            candidate_endpoint, candidate_payload = attempt_candidates[idx]

            async def producer() -> None:
                nonlocal last_error
                try:
                    async for pcm in self._stream_with_retries(
                        endpoint=candidate_endpoint,
                        payload=candidate_payload,
                        text_len=text_len,
                    ):
                        await queue.put(pcm)
                except Exception as exc:  # noqa: PERF203
                    candidate.error = exc
                    last_error = exc
                finally:
                    await queue.put(None)

            candidate.task = asyncio.create_task(producer())
            self._last_attempt_count = max(self._last_attempt_count, idx + 1)
            return candidate

        async def _cancel_candidates(candidates: list[_RaceCandidate]) -> None:
            tasks: list[asyncio.Task[None]] = []
            for candidate in candidates:
                if candidate.task and not candidate.task.done():
                    candidate.task.cancel()
                if candidate.task:
                    tasks.append(candidate.task)
            if not tasks:
                return

            done, pending = await asyncio.wait(tasks, timeout=0.3)
            for task in pending:
                task.cancel()
            for task in done:
                try:
                    await task
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.warning(
                        "Error awaiting cancelled TTS candidate text_len=%s: %s",
                        text_len,
                        repr(e),
                    )

        async def _launch_next_candidate() -> bool:
            nonlocal next_idx, next_launch_at, launched_count
            if next_idx >= len(attempt_candidates) or len(active) >= max_racers:
                return False
            candidate = await _start_candidate(next_idx)
            active.append(candidate)
            next_idx += 1
            launched_count += 1
            self._last_hedge_racers = launched_count
            next_launch_at = time.perf_counter() + hedge_delay_seconds
            if candidate.idx > 0:
                candidate_endpoint, _ = attempt_candidates[candidate.idx]
                logger.info(
                    "TTS hedge launched racer endpoint=%s text_len=%s racer=%s delay=%.3fs",
                    candidate_endpoint,
                    text_len,
                    candidate.idx + 1,
                    hedge_delay_seconds,
                )
            return True

        await _launch_next_candidate()

        winner: _RaceCandidate | None = None
        winner_first_chunk: bytes | None = None

        while winner is None:
            if not active:
                launched = await _launch_next_candidate()
                if not launched:
                    break

            get_tasks: dict[asyncio.Task[bytes | None], _RaceCandidate] = {
                asyncio.create_task(candidate.queue.get()): candidate
                for candidate in active
            }

            timeout: float | None = None
            if next_idx < len(attempt_candidates) and len(active) < max_racers:
                timeout = max(0.0, next_launch_at - time.perf_counter())

            done, pending = await asyncio.wait(
                list(get_tasks.keys()),
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for pending_task in pending:
                pending_task.cancel()
            for pending_task in pending:
                with suppress(asyncio.CancelledError):
                    await pending_task

            if not done:
                await _launch_next_candidate()
                continue

            for task in done:
                candidate = get_tasks[task]
                item = task.result()
                if item is None:
                    if candidate.task:
                        await candidate.task
                    if candidate in active:
                        active.remove(candidate)
                    if candidate.error is not None:
                        last_error = candidate.error
                    continue

                if winner is None:
                    winner = candidate
                    winner_first_chunk = item

            if winner is not None:
                break

        if winner is None:
            await _cancel_candidates(active)
            if last_error is not None:
                raise last_error
            raise RuntimeError("tts_hedge_no_audio")

        losers = [candidate for candidate in active if candidate is not winner]
        cancel_losers_task: asyncio.Task[None] | None = None

        if winner_first_chunk is not None:
            yielded_any = True
            yield winner_first_chunk

        if losers:
            cancel_losers_task = asyncio.create_task(_cancel_candidates(losers))

        while True:
            try:
                item = await asyncio.wait_for(
                    winner.queue.get(), timeout=self._request_timeout_seconds
                )
            except asyncio.TimeoutError as exc:
                if winner.task and not winner.task.done():
                    winner.task.cancel()
                    with suppress(asyncio.CancelledError):
                        await winner.task
                raise RuntimeError(
                    f"tts_sentence_timeout len={text_len} timeout={self._request_timeout_seconds}s"
                ) from exc

            if item is None:
                break
            yielded_any = True
            yield item

        if winner.task:
            await winner.task
        if cancel_losers_task is not None:
            with suppress(asyncio.CancelledError):
                await cancel_losers_task
        if winner.error is not None:
            if yielded_any:
                winner_endpoint, _ = attempt_candidates[winner.idx]
                logger.warning(
                    "TTS hedge winner ended early endpoint=%s text_len=%s error=%s",
                    winner_endpoint,
                    text_len,
                    winner.error,
                )
                return
            raise winner.error

    def _split_for_quality(self, sentence: str) -> list[str]:
        text = sentence.strip()
        if not text:
            return []

        max_chars = max(24, int(getattr(settings, "TTS_SENTENCE_MAX_CHARS", 120)))
        soft_chars = max(
            12, min(max_chars, int(getattr(settings, "TTS_SENTENCE_SOFT_CHARS", 64)))
        )

        if _has_english(text):
            max_chars = min(max_chars, 48)
            soft_chars = min(soft_chars, 28)

        if len(text) <= max_chars:
            return [text]

        parts: list[str] = []
        cursor = text
        while cursor:
            if len(cursor) <= max_chars:
                parts.append(cursor.strip())
                break

            split_idx = -1
            search_end = min(max_chars, len(cursor))
            for idx in range(search_end - 1, soft_chars - 2, -1):
                if cursor[idx] in {
                    "。",
                    "！",
                    "？",
                    "；",
                    ";",
                    "，",
                    ",",
                    " ",
                    "、",
                    ":",
                    "：",
                }:
                    split_idx = idx
                    break

            if split_idx < 0:
                split_idx = max_chars - 1

            part = cursor[: split_idx + 1].strip()
            if part:
                parts.append(part)
            cursor = cursor[split_idx + 1 :].strip()

        parts = [p for p in parts if p]
        return self._limit_first_chunk_complexity(parts)

    def _limit_first_chunk_complexity(self, parts: list[str]) -> list[str]:
        if not parts:
            return parts

        first = parts[0].strip()
        if len(first) <= 30 and _END_PUNCT_RE.search(first):
            return parts

        split_idx = -1
        for idx, ch in enumerate(first):
            if ch in {"。", "！", "？", "!", "?", "；", ";"}:
                split_idx = idx
                if idx + 1 >= 15:
                    break

        if split_idx < 0:
            for idx, ch in enumerate(first):
                if ch in {"，", ",", "、", "：", ":", " "} and idx + 1 >= 15:
                    split_idx = idx
                    break

        if split_idx < 0:
            split_idx = min(len(first) - 1, 40)

        head = first[: split_idx + 1].strip()
        tail = first[split_idx + 1 :].strip()
        new_parts: list[str] = []
        if head:
            new_parts.append(head)
        if tail:
            new_parts.append(tail)
        new_parts.extend(parts[1:])
        return new_parts

    async def _warm_if_needed(self) -> None:
        now = time.perf_counter()
        if now < self._warmed_recently_until:
            return

        async with self._warm_lock:
            now = time.perf_counter()
            if now < self._warmed_recently_until:
                return

            active_mode = self._active_mode()
            endpoint = self._resolve_endpoint(active_mode)
            payload = self._build_payload_for_mode("嗯。", active_mode)
            warm_started_at = time.perf_counter()
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        self._warm_timeout_seconds,
                        connect=min(0.5, self._warm_timeout_seconds),
                    )
                ) as client:
                    async with client.stream(
                        "POST", endpoint, data=payload
                    ) as response:
                        if response.status_code < 400:
                            async for chunk in response.aiter_bytes():
                                if chunk:
                                    break
                self._warmed_recently_until = (
                    time.perf_counter() + self._warm_keepalive_seconds
                )
                logger.debug(
                    "TTS warmup ok endpoint=%s cost=%.3fs keepalive=%.1fs",
                    endpoint,
                    time.perf_counter() - warm_started_at,
                    self._warm_keepalive_seconds,
                )
            except Exception:
                if active_mode == "instruct":
                    self._mark_instruct_unavailable()
                self._warmed_recently_until = time.perf_counter() + 5.0
                logger.debug(
                    "TTS warmup failed endpoint=%s timeout=%.2fs, retry soon",
                    endpoint,
                    self._warm_timeout_seconds,
                )

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
        resolved_speed = self._resolve_speed_for_text(text)
        raw = (
            f"{_TTS_CACHE_SCHEMA}|{settings.TTS_BACKEND}|{settings.COSYVOICE_BASE_URL}|"
            f"{self._resolve_endpoint()}|{settings.COSYVOICE_VOICE}|{self._mode}|"
            f"{self._instruct_text}|"
            f"{settings.COSYVOICE_SAMPLE_RATE}|{resolved_speed:.4f}|"
            f"{settings.COSYVOICE_SEED}|{text}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _resolve_endpoint(self, mode: str | None = None) -> str:
        resolved_mode = (mode or self._mode).strip().lower()
        if resolved_mode == "instruct":
            return f"{self._base_url}/inference_instruct"
        return f"{self._base_url}{self._tts_path}"

    def _build_payload(self, text: str) -> dict[str, object]:
        return self._build_payload_for_mode(text, self._mode)

    def _active_mode(self) -> str:
        if self._mode != "instruct":
            return self._mode
        if time.perf_counter() < self._instruct_unavailable_until:
            return "sft"
        return "instruct"

    def _mark_instruct_unavailable(self, cooldown: float | None = None) -> None:
        duration = cooldown if cooldown is not None else self._instruct_backoff_seconds
        duration = max(5.0, float(duration))
        self._instruct_unavailable_until = max(
            self._instruct_unavailable_until,
            time.perf_counter() + duration,
        )
        logger.warning("CosyVoice instruct mode backoff enabled for %.0fs", duration)

    def _build_payload_for_mode(self, text: str, mode: str) -> dict[str, object]:
        speed = self._resolve_speed_for_text(text)
        payload: dict[str, object] = {
            "tts_text": text,
            "spk_id": settings.COSYVOICE_VOICE,
            "seed": self._fixed_seed,
            "speed": speed,
            **self._extra_payload,
        }

        if mode == "instruct" and self._instruct_text:
            payload["instruct_text"] = self._instruct_text

        return payload

    def _resolve_speed_for_text(self, text: str) -> float:
        speed = float(self._speed)
        alpha_count = len(_EN_LETTER_RE.findall(text))
        cjk_count = len(_CJK_RE.findall(text))

        if cjk_count >= 40 and alpha_count == 0:
            speed = min(speed, 1.65)
        if alpha_count > 0:
            speed = min(speed, 1.4)
        if alpha_count >= 6:
            speed = min(speed, 1.3)
        if alpha_count == 0 and 0 < cjk_count <= 8:
            speed = max(speed, min(1.72, float(self._speed) + 0.12))
        if alpha_count == 0 and 0 < cjk_count <= 4:
            speed = max(speed, min(1.8, float(self._speed) + 0.2))

        return min(1.85, max(1.15, speed))

    def _resolve_hedge_delay_for_text(
        self,
        text: str,
    ) -> float:
        delay = float(self._hedge_delay_seconds)
        alpha_count = len(_EN_LETTER_RE.findall(text))
        cjk_count = len(_CJK_RE.findall(text))

        # Very short texts get faster hedge
        if cjk_count <= 10 and alpha_count == 0:
            delay = max(0.15, delay - 0.2)
        elif alpha_count > 0:
            delay = min(delay, 0.4)
        elif cjk_count >= 26:
            delay = min(delay, 0.5)
        elif cjk_count <= 8 and alpha_count == 0:
            delay = max(delay, 0.6)

        return max(0.1, delay)

    def _should_enable_hedge(
        self,
        text: str,
        attempt_candidates: list[tuple[str, dict[str, object]]],
        *,
        is_first_segment: bool,
    ) -> bool:
        if not self._hedge_enabled:
            return False
        if len(attempt_candidates) < 2:
            return False
        return True

    async def _stream_with_retries(
        self,
        *,
        endpoint: str,
        payload: dict[str, object],
        text_len: int,
    ) -> AsyncIterator[bytes]:
        attempts = 3
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
                                    "CosyVoice first chunk latency endpoint=%s text_len=%s latency=%.3fs",
                                    endpoint,
                                    text_len,
                                    first_chunk_at - stream_start,
                                )
                            yield chunk

                        if pending_byte:
                            logger.warning(
                                "CosyVoice stream ended with odd trailing byte; dropping for PCM alignment text_len=%s",
                                text_len,
                            )

                        if chunk_count == 0:
                            raise RuntimeError("CosyVoice stream returned no chunks")
                        logger.info(
                            "CosyVoice stream completed endpoint=%s text_len=%s chunks=%s total=%.3fs",
                            endpoint,
                            text_len,
                            chunk_count,
                            time.perf_counter() - stream_start,
                        )
                        return
            except Exception as exc:
                if yielded_any:
                    logger.warning(
                        "CosyVoice stream ended early endpoint=%s text_len=%s error=%s",
                        endpoint,
                        text_len,
                        exc,
                    )
                    return

                if attempt >= attempts:
                    logger.exception(
                        "CosyVoice stream failed endpoint=%s text_len=%s error=%s",
                        endpoint,
                        text_len,
                        exc,
                    )
                    raise RuntimeError("cosyvoice_stream_failed") from exc

                await asyncio.sleep(0.2 * attempt)

    async def _probe_stream_chunk(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        payload: dict[str, object],
    ) -> bool:
        try:
            chunk_seen = False
            async with client.stream("POST", endpoint, data=payload) as probe:
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
            logger.warning("CosyVoice probe error endpoint=%s error=%s", endpoint, exc)
            return False

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

    def _wav_to_pcm_if_needed(self, audio_bytes: bytes) -> bytes:
        if not audio_bytes:
            return b""
        if not (
            len(audio_bytes) >= 12
            and audio_bytes[:4] == b"RIFF"
            and audio_bytes[8:12] == b"WAVE"
        ):
            return audio_bytes

        try:
            with wave.open(BytesIO(audio_bytes), "rb") as src:
                frames = src.readframes(src.getnframes())
                if len(frames) % 2 != 0:
                    frames = frames[:-1]
                return frames
        except Exception as exc:
            logger.warning("Failed to decode WAV cache as PCM: %s", exc)
            return audio_bytes

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

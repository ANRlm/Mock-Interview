from __future__ import annotations

import argparse
import sys
import asyncio
import base64
import json
import os
import struct
import wave
from pathlib import Path
from typing import Any

import httpx
import websockets


def _disable_local_proxy_env() -> None:
    proxy_keys = (
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "ws_proxy",
        "wss_proxy",
        "WS_PROXY",
        "WSS_PROXY",
    )
    for key in proxy_keys:
        os.environ.pop(key, None)


def _ws_to_http_base(ws_base: str) -> str:
    if ws_base.startswith("ws://"):
        return "http://" + ws_base[5:]
    if ws_base.startswith("wss://"):
        return "https://" + ws_base[6:]
    raise ValueError(f"Unsupported ws base url: {ws_base}")


def _build_test_pcm_base64(sample_rate: int = 16000, seconds: float = 0.6) -> str:
    frame_count = int(sample_rate * seconds)
    freq_hz = 220.0
    amplitude = 9000
    pcm = bytearray()
    for i in range(frame_count):
        value = int(
            amplitude
            * __import__("math").sin(
                2 * __import__("math").pi * freq_hz * i / sample_rate
            )
        )
        pcm.extend(struct.pack("<h", value))
    return base64.b64encode(bytes(pcm)).decode("utf-8")


async def _build_tts_pcm_base64() -> tuple[str, int]:
    cosy_base = os.getenv("COSYVOICE_BASE_URL", "http://cosyvoice2:50000").rstrip("/")
    cosy_path = os.getenv("COSYVOICE_TTS_PATH", "/inference_sft").strip()
    cosy_voice = os.getenv("COSYVOICE_VOICE", "default_zh")
    cosy_sample_rate = int(os.getenv("COSYVOICE_SAMPLE_RATE", "22050"))

    if not cosy_path.startswith("/"):
        cosy_path = "/" + cosy_path

    endpoint = f"{cosy_base}{cosy_path}"
    payload = {
        "tts_text": "你好，我想回答这个问题。",
        "spk_id": cosy_voice,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=20.0)) as client:
        response = await client.post(endpoint, data=payload)
        response.raise_for_status()
        pcm_bytes = response.content

    if not pcm_bytes:
        raise RuntimeError("empty_tts_pcm")

    return base64.b64encode(pcm_bytes).decode("utf-8"), cosy_sample_rate


def _save_wav(path: Path, b64_wav: str) -> None:
    raw = base64.b64decode(b64_wav.encode("utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _new_client(*, timeout: httpx.Timeout | float, token: str | None = None) -> httpx.AsyncClient:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.AsyncClient(timeout=timeout, trust_env=False, headers=headers)


async def _login(api_base: str, email: str, password: str) -> str:
    async with _new_client(timeout=20.0) as client:
        response = await client.post(
            f"{api_base}/auth/login",
            json={"email": email, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]


async def _create_session(api_base: str, token: str) -> dict[str, Any]:
    async with _new_client(timeout=20.0, token=token) as client:
        response = await client.post(
            f"{api_base}/sessions",
            json={"job_role": "programmer", "sub_role": "frontend engineer"},
        )
        response.raise_for_status()
        return response.json()


async def _upload_resume(api_base: str, session_id: str, token: str) -> dict[str, Any]:
    resume_text = """张三\n教育经历：某大学 计算机科学本科\n工作经历：负责前端架构与性能优化\n项目经历：主导企业级低代码平台\n技能：React TypeScript Node.js\n"""
    files = {
        "file": (
            "resume.txt",
            resume_text.encode("utf-8"),
            "text/plain",
        )
    }
    async with _new_client(timeout=httpx.Timeout(240.0, connect=20.0), token=token) as client:
        response = await client.post(
            f"{api_base}/sessions/{session_id}/resume",
            files=files,
        )
        response.raise_for_status()
        return response.json()


async def _run_ws_round(
    ws_base: str,
    session_id: str,
    token: str,
    *,
    recv_timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    ws_url = f"{ws_base}/interview/{session_id}?token={token}"
    llm_tokens: list[str] = []
    current_response_id = ""
    tts_first_audio_seconds: float | None = None
    llm_start_at: float | None = None
    first_llm_token_at: float | None = None
    tts_chunks = 0
    stt_partial = 0
    stt_final = ""
    tts_first_wav: str | None = None
    llm_done = False
    tts_done = False
    llm_stats: dict[str, Any] | None = None

    async with websockets.connect(ws_url, close_timeout=30.0) as ws:
        llm_start_at = asyncio.get_running_loop().time()
        await ws.send(
            json.dumps(
                {"type": "candidate_message", "text": "请先问我一个前端项目相关问题"}
            )
        )

        loop_guard = 0
        while not tts_done and loop_guard < 600:
            loop_guard += 1
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=recv_timeout_seconds)
            except asyncio.TimeoutError as exc:
                raise RuntimeError(
                    "ws_timeout "
                    f"stage=llm_tts session={session_id} timeout={recv_timeout_seconds}s "
                    f"llm_tokens={len(llm_tokens)} llm_done={llm_done} tts_chunks={tts_chunks}"
                ) from exc
            if isinstance(raw, bytes):
                continue

            payload = json.loads(raw)
            msg_type = payload.get("type")

            if msg_type == "llm_token":
                rid = str(payload.get("response_id") or "")
                if rid and not current_response_id:
                    current_response_id = rid
                if rid and current_response_id and rid != current_response_id:
                    continue
                token = str(payload.get("token") or "")
                if token and first_llm_token_at is None:
                    first_llm_token_at = asyncio.get_running_loop().time()
                llm_tokens.append(token)
            elif msg_type == "llm_done":
                rid = str(payload.get("response_id") or "")
                if rid and not current_response_id:
                    current_response_id = rid
                if rid and current_response_id and rid != current_response_id:
                    continue
                llm_done = True
            elif msg_type == "llm_stats":
                llm_stats = payload
            elif msg_type == "tts_audio":
                rid = str(payload.get("response_id") or "")
                if rid and current_response_id and rid != current_response_id:
                    continue
                tts_chunks += 1
                if tts_first_wav is None:
                    tts_first_wav = str(payload.get("data") or "")
                    if llm_start_at is not None:
                        tts_first_audio_seconds = (
                            asyncio.get_running_loop().time() - llm_start_at
                        )
            elif msg_type == "tts_done":
                rid = str(payload.get("response_id") or "")
                if rid and current_response_id and rid != current_response_id:
                    continue
                tts_done = True
            elif msg_type == "error":
                raise RuntimeError(f"ws_error: {payload}")

        try:
            stt_pcm_b64, stt_sample_rate = await _build_tts_pcm_base64()
        except Exception:
            stt_pcm_b64 = _build_test_pcm_base64()
            stt_sample_rate = 16000

        await ws.send(
            json.dumps(
                {
                    "type": "audio_chunk",
                    "data": stt_pcm_b64,
                    "sample_rate": stt_sample_rate,
                }
            )
        )
        await ws.send(json.dumps({"type": "audio_end"}))

        loop_guard = 0
        got_stt_final = False
        while loop_guard < 600:
            loop_guard += 1
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=recv_timeout_seconds)
            except asyncio.TimeoutError as exc:
                raise RuntimeError(
                    "ws_timeout "
                    f"stage=stt session={session_id} timeout={recv_timeout_seconds}s "
                    f"stt_partial={stt_partial}"
                ) from exc
            if isinstance(raw, bytes):
                continue

            payload = json.loads(raw)
            msg_type = payload.get("type")
            if msg_type == "stt_partial":
                stt_partial += 1
            elif msg_type == "stt_final":
                stt_final = str(payload.get("text") or "")
                got_stt_final = True
                break
            elif msg_type == "error":
                raise RuntimeError(f"ws_error: {payload}")

        if not got_stt_final:
            raise RuntimeError("stt_final_not_received")
        if not stt_final.strip():
            raise RuntimeError("stt_final_empty")

    return {
        "llm_tokens": len([token for token in llm_tokens if token]),
        "llm_done": llm_done,
        "llm_stats": llm_stats or {},
        "tts_chunks": tts_chunks,
        "tts_first_audio_seconds": tts_first_audio_seconds,
        "tts_audio_start_ref": "llm_start",
        "llm_first_token_seconds": (
            (first_llm_token_at - llm_start_at)
            if (first_llm_token_at is not None and llm_start_at is not None)
            else None
        ),
        "tts_after_first_token_seconds": (
            (tts_first_audio_seconds - (first_llm_token_at - llm_start_at))
            if (
                tts_first_audio_seconds is not None
                and first_llm_token_at is not None
                and llm_start_at is not None
            )
            else None
        ),
        "tts_first_wav": tts_first_wav,
        "stt_partial_events": stt_partial,
        "stt_final": stt_final,
    }


async def _generate_report(api_base: str, session_id: str, token: str) -> dict[str, Any]:
    async with _new_client(timeout=30.0, token=token) as client:
        trigger = await client.post(f"{api_base}/sessions/{session_id}/report")
        trigger.raise_for_status()

        for _ in range(180):
            report_response = await client.get(
                f"{api_base}/sessions/{session_id}/report"
            )
            if report_response.status_code == 200:
                return report_response.json()
            if report_response.status_code not in {202, 404}:
                report_response.raise_for_status()
            await asyncio.sleep(2.0)

    raise RuntimeError("report_timeout")


async def _fetch_tts_metrics(api_base: str, token: str) -> dict[str, Any]:
    async with _new_client(timeout=20.0, token=token) as client:
        response = await client.get(f"{api_base}/tts/metrics")
        response.raise_for_status()
        payload = response.json()

    keep_keys = {
        "count",
        "session_count",
        "session_success",
        "first_audio",
        "provider_first_chunk",
        "attempts",
        "hedge",
        "latency_buckets",
    }
    if not isinstance(payload, dict):
        return {}
    return {k: payload.get(k) for k in keep_keys if k in payload}


async def _reset_tts_metrics(api_base: str, token: str) -> None:
    async with _new_client(timeout=20.0, token=token) as client:
        response = await client.delete(f"{api_base}/tts/metrics")
        response.raise_for_status()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Phase1-3 smoke test")
    parser.add_argument(
        "--api-base", default=os.getenv("SMOKE_API_BASE", "http://127.0.0.1:8000/api")
    )
    parser.add_argument(
        "--ws-base", default=os.getenv("SMOKE_WS_BASE", "ws://127.0.0.1:8000/ws")
    )
    parser.add_argument(
        "--artifact-dir", default=os.getenv("SMOKE_ARTIFACT_DIR", "/tmp/phase123_smoke")
    )
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument(
        "--ws-recv-timeout",
        type=float,
        default=float(os.getenv("SMOKE_WS_RECV_TIMEOUT_SECONDS", "120")),
    )
    parser.add_argument("--reset-tts-metrics", action="store_true")
    parser.add_argument("--email", default=os.getenv("SMOKE_EMAIL", "smoketest@test.local"))
    parser.add_argument("--password", default=os.getenv("SMOKE_PASSWORD", "smoketest123"))
    parser.add_argument("--register", action="store_true", help="Register the test user if not exists")
    args = parser.parse_args()

    _disable_local_proxy_env()

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    api_base = args.api_base.rstrip("/")
    ws_base = args.ws_base.rstrip("/")
    http_health_base = _ws_to_http_base(ws_base)
    if http_health_base.endswith("/ws"):
        http_health_base = http_health_base[: -len("/ws")]

    async with _new_client(timeout=20.0) as client:
        backend_health = await client.get(f"{http_health_base}/healthz")
        backend_health.raise_for_status()

    if args.register:
        async with _new_client(timeout=20.0) as client:
            try:
                reg_resp = await client.post(
                    f"{api_base}/auth/register",
                    json={
                        "email": args.email,
                        "password": args.password,
                    },
                )
                if reg_resp.status_code == 201:
                    print(f"Registered: {args.email}", file=sys.stderr)
                elif reg_resp.status_code == 409:
                    print(f"Already registered: {args.email}", file=sys.stderr)
                else:
                    reg_resp.raise_for_status()
            except Exception as exc:
                print(f"Registration warning: {exc}", file=sys.stderr)

    token = await _login(api_base, args.email, args.password)
    print(f"Authenticated as: {args.email}", file=sys.stderr)

    if args.reset_tts_metrics:
        await _reset_tts_metrics(api_base, token)

    outputs: list[dict[str, Any]] = []
    failed_runs: list[dict[str, str]] = []
    for _ in range(max(1, args.runs)):
        session = await _create_session(api_base, token)
        session_id = str(session["id"])

        try:
            resume = await _upload_resume(api_base, session_id, token)
            ws_result = await _run_ws_round(
                ws_base,
                session_id,
                token,
                recv_timeout_seconds=max(30.0, float(args.ws_recv_timeout)),
            )
            report = await _generate_report(api_base, session_id, token)
        except Exception as exc:
            failed_runs.append({"session_id": session_id, "error": str(exc)})
            continue

        wav_saved = ""
        if ws_result.get("tts_first_wav"):
            wav_path = artifact_dir / f"{session_id}_tts_first_chunk.wav"
            _save_wav(wav_path, str(ws_result["tts_first_wav"]))
            wav_saved = str(wav_path)

        output = {
            "session_id": session_id,
            "resume_status": resume.get("status"),
            "llm_tokens": ws_result.get("llm_tokens"),
            "llm_done": ws_result.get("llm_done"),
            "llm_stats": ws_result.get("llm_stats"),
            "tts_chunks": ws_result.get("tts_chunks"),
            "tts_first_audio_seconds": ws_result.get("tts_first_audio_seconds"),
            "llm_first_token_seconds": ws_result.get("llm_first_token_seconds"),
            "tts_after_first_token_seconds": ws_result.get(
                "tts_after_first_token_seconds"
            ),
            "stt_partial_events": ws_result.get("stt_partial_events"),
            "stt_final": ws_result.get("stt_final"),
            "report_total_score": report.get("total_score"),
            "report_generated_at": report.get("generated_at"),
            "tts_first_chunk_wav": wav_saved,
        }

        result_path = artifact_dir / f"{session_id}_result.json"
        result_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        outputs.append(output)

    if len(outputs) == 1:
        print(json.dumps(outputs[0], ensure_ascii=False))
        return

    latencies = [
        float(item["tts_first_audio_seconds"])
        for item in outputs
        if isinstance(item.get("tts_first_audio_seconds"), (int, float))
    ]
    post_token_latencies = [
        float(item["tts_after_first_token_seconds"])
        for item in outputs
        if isinstance(item.get("tts_after_first_token_seconds"), (int, float))
    ]
    summary: dict[str, Any] = {
        "requested_runs": max(1, args.runs),
        "runs": len(outputs),
        "failed_runs": failed_runs,
        "failed_count": len(failed_runs),
        "sessions": [item["session_id"] for item in outputs],
    }
    if latencies:
        sorted_vals = sorted(latencies)
        n = len(sorted_vals)
        median = (
            sorted_vals[n // 2]
            if n % 2 == 1
            else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        )
        p90_idx = min(n - 1, max(0, int(n * 0.9) - 1))
        p99_idx = min(n - 1, max(0, int(n * 0.99) - 1))
        summary.update(
            {
                "tts_first_audio_seconds": {
                    "min": round(min(sorted_vals), 3),
                    "p50": round(median, 3),
                    "p90": round(sorted_vals[p90_idx], 3),
                    "p99": round(sorted_vals[p99_idx], 3),
                    "max": round(max(sorted_vals), 3),
                    "raw": [round(v, 3) for v in latencies],
                }
            }
        )

    if post_token_latencies:
        sorted_post = sorted(post_token_latencies)
        n_post = len(sorted_post)
        median_post = (
            sorted_post[n_post // 2]
            if n_post % 2 == 1
            else (sorted_post[n_post // 2 - 1] + sorted_post[n_post // 2]) / 2
        )
        p90_post = min(n_post - 1, max(0, int(n_post * 0.9) - 1))
        p99_post = min(n_post - 1, max(0, int(n_post * 0.99) - 1))
        summary["tts_after_first_token_seconds"] = {
            "min": round(min(sorted_post), 3),
            "p50": round(median_post, 3),
            "p90": round(sorted_post[p90_post], 3),
            "p99": round(sorted_post[p99_post], 3),
            "max": round(max(sorted_post), 3),
            "raw": [round(v, 3) for v in post_token_latencies],
        }

    try:
        summary["tts_metrics"] = await _fetch_tts_metrics(api_base, token)
    except Exception as exc:
        summary["tts_metrics_error"] = str(exc)

    summary_path = artifact_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

import argparse
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


async def _create_session(api_base: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{api_base}/sessions",
            json={"job_role": "programmer", "sub_role": "frontend engineer"},
        )
        response.raise_for_status()
        return response.json()


async def _upload_resume(api_base: str, session_id: str) -> dict[str, Any]:
    resume_text = """张三\n教育经历：某大学 计算机科学本科\n工作经历：负责前端架构与性能优化\n项目经历：主导企业级低代码平台\n技能：React TypeScript Node.js\n"""
    files = {
        "file": (
            "resume.txt",
            resume_text.encode("utf-8"),
            "text/plain",
        )
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(240.0, connect=20.0)) as client:
        response = await client.post(
            f"{api_base}/sessions/{session_id}/resume",
            files=files,
        )
        response.raise_for_status()
        return response.json()


async def _run_ws_round(ws_base: str, session_id: str) -> dict[str, Any]:
    ws_url = f"{ws_base}/interview/{session_id}"
    llm_tokens: list[str] = []
    tts_chunks = 0
    stt_partial = 0
    stt_final = ""
    tts_first_wav: str | None = None
    llm_done = False
    tts_done = False
    llm_stats: dict[str, Any] | None = None

    async with websockets.connect(ws_url, close_timeout=30.0) as ws:
        await ws.send(
            json.dumps(
                {"type": "candidate_message", "text": "请先问我一个前端项目相关问题"}
            )
        )

        loop_guard = 0
        while not tts_done and loop_guard < 600:
            loop_guard += 1
            raw = await asyncio.wait_for(ws.recv(), timeout=60.0)
            if isinstance(raw, bytes):
                continue

            payload = json.loads(raw)
            msg_type = payload.get("type")

            if msg_type == "llm_token":
                llm_tokens.append(str(payload.get("token") or ""))
            elif msg_type == "llm_done":
                llm_done = True
            elif msg_type == "llm_stats":
                llm_stats = payload
            elif msg_type == "tts_audio":
                tts_chunks += 1
                if tts_first_wav is None:
                    tts_first_wav = str(payload.get("data") or "")
            elif msg_type == "tts_done":
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
            raw = await asyncio.wait_for(ws.recv(), timeout=60.0)
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
        "tts_first_wav": tts_first_wav,
        "stt_partial_events": stt_partial,
        "stt_final": stt_final,
    }


async def _generate_report(api_base: str, session_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
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
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    api_base = args.api_base.rstrip("/")
    ws_base = args.ws_base.rstrip("/")
    http_health_base = _ws_to_http_base(ws_base)
    if http_health_base.endswith("/ws"):
        http_health_base = http_health_base[: -len("/ws")]

    async with httpx.AsyncClient(timeout=20.0) as client:
        backend_health = await client.get(f"{http_health_base}/healthz")
        backend_health.raise_for_status()

    session = await _create_session(api_base)
    session_id = str(session["id"])

    resume = await _upload_resume(api_base, session_id)
    ws_result = await _run_ws_round(ws_base, session_id)
    report = await _generate_report(api_base, session_id)

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

    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Measure baseline latency for STT, LLM, TTS components."""
import asyncio
import json
import time
from pathlib import Path


async def measure_stt_latency():
    """Measure STT latency."""
    from app.services.stt_service import stt_service
    start = time.perf_counter()
    pcm = b'\x00' * 16000 * 2  # 2 seconds placeholder
    try:
        async for evt, text in stt_service.transcribe_stream_events(pcm):
            elapsed = (time.perf_counter() - start) * 1000
            return {"stt_ms": round(elapsed, 1), "event": evt, "text": (text[:50] or "") if text else ""}
        elapsed = (time.perf_counter() - start) * 1000
        return {"stt_ms": round(elapsed, 1)}
    except Exception as e:
        return {"stt_ms": -1, "error": str(e)}


async def measure_llm_latency():
    """Measure LLM first token latency."""
    from app.agents.interviewer_agent import InterviewerAgent
    start = time.perf_counter()
    messages = [{"role": "user", "content": "请自我介绍"}]
    first_token_time = None
    try:
        agent = InterviewerAgent()
        stream = await agent.chat(messages, stream=True)
        async for chunk in stream:
            if first_token_time is None:
                first_token_time = time.perf_counter()
        total = (time.perf_counter() - start) * 1000
        first = (first_token_time - start) * 1000 if first_token_time else total
        return {"llm_first_token_ms": round(first, 1), "llm_total_ms": round(total, 1)}
    except Exception as e:
        return {"llm_first_token_ms": -1, "llm_total_ms": -1, "error": str(e)}


async def measure_tts_latency():
    """Measure TTS first chunk latency."""
    from app.services.tts_service import tts_service
    start = time.perf_counter()
    first_chunk_time = None
    try:
        async for chunk in tts_service.stream_synthesize("你好"):
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter()
        total = (time.perf_counter() - start) * 1000
        first = (first_chunk_time - start) * 1000 if first_chunk_time else total
        return {"tts_first_chunk_ms": round(first, 1), "tts_total_ms": round(total, 1)}
    except Exception as e:
        return {"tts_first_chunk_ms": -1, "tts_total_ms": -1, "error": str(e)}


async def main():
    output = Path(".sisyphus/evidence/baseline_metrics.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    results = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}

    results["stt"] = await measure_stt_latency()
    results["llm"] = await measure_llm_latency()
    results["tts"] = await measure_tts_latency()

    stt_ms = results.get("stt", {}).get("stt_ms", 0) or 0
    llm_ms = results.get("llm", {}).get("llm_first_token_ms", 0) or 0
    tts_ms = results.get("tts", {}).get("tts_first_chunk_ms", 0) or 0

    if stt_ms > 0 and llm_ms > 0 and tts_ms > 0:
        results["e2e_estimate_ms"] = round(stt_ms + llm_ms + tts_ms, 1)
    else:
        results["e2e_estimate_ms"] = -1

    output.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
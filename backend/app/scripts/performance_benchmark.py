#!/usr/bin/env python3
"""Performance benchmark for optimized voice pipeline."""
import asyncio
import json
import time
import os
from pathlib import Path

# Disable proxy for local testing
def _disable_local_proxy_env() -> None:
    proxy_keys = (
        "http_proxy", "https_proxy", "all_proxy",
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "ws_proxy", "wss_proxy", "WS_PROXY", "WSS_PROXY",
    )
    for key in proxy_keys:
        os.environ.pop(key, None)

_disable_local_proxy_env()


async def benchmark_llm_latency():
    """Benchmark LLM first token and total latency."""
    from app.agents.interviewer_agent import InterviewerAgent
    from app.models.session import JobRole

    results = {}

    agent = InterviewerAgent()
    messages = [
        {"role": "user", "content": "请自我介绍"}
    ]

    # Warm-up call
    try:
        warmup_stream = await agent.chat(messages, stream=True)
        async for _ in warmup_stream:
            pass
    except Exception:
        pass

    # Benchmark call
    start = time.perf_counter()
    first_token = None
    total_tokens = 0

    try:
        stream = await agent.chat(messages, stream=True)
        async for token in stream:
            if first_token is None:
                first_token = time.perf_counter() - start
            total_tokens += 1
        total_time = time.perf_counter() - start

        results["llm_first_token_ms"] = round(first_token * 1000, 1) if first_token else None
        results["llm_total_ms"] = round(total_time * 1000, 1)
        results["llm_total_tokens"] = total_tokens
        results["llm_tokens_per_second"] = round(total_tokens / total_time, 1) if total_time > 0 else None
    except Exception as e:
        results["llm_error"] = str(e)

    return results


async def benchmark_tts_latency():
    """Benchmark TTS first chunk and total latency."""
    from app.services.qwen_tts_service import qwen_tts_service

    results = {}
    test_text = "你好，很高兴认识你。"

    # Warm-up call
    try:
        warmup_stream = qwen_tts_service.stream_synthesize(test_text)
        async for _ in warmup_stream:
            pass
    except Exception:
        pass

    # Benchmark call
    start = time.perf_counter()
    first_chunk = None
    total_chunks = 0

    try:
        stream = qwen_tts_service.stream_synthesize(test_text)
        async for chunk in stream:
            if first_chunk is None:
                first_chunk = time.perf_counter() - start
            total_chunks += 1
        total_time = time.perf_counter() - start

        results["tts_first_chunk_ms"] = round(first_chunk * 1000, 1) if first_chunk else None
        results["tts_total_ms"] = round(total_time * 1000, 1)
        results["tts_total_chunks"] = total_chunks
    except Exception as e:
        results["tts_error"] = str(e)

    return results


async def benchmark_stt_latency():
    """Benchmark STT transcription latency."""
    from app.services.paraformer_stt_service import paraformer_stt_service

    results = {}

    # Generate test PCM audio (0.5 seconds of 220Hz sine wave)
    import struct
    import math
    import base64

    sample_rate = 16000
    seconds = 0.5
    frame_count = int(sample_rate * seconds)
    freq_hz = 220.0
    amplitude = 9000

    pcm = bytearray()
    for i in range(frame_count):
        value = int(amplitude * math.sin(2 * math.pi * freq_hz * i / sample_rate))
        pcm.extend(struct.pack("<h", value))

    pcm_bytes = bytes(pcm)

    # Benchmark call
    start = time.perf_counter()
    first_result = None

    try:
        stream = paraformer_stt_service.transcribe_streaming(pcm_bytes)
        async for evt, text in stream:
            if first_result is None:
                first_result = time.perf_counter() - start
            if evt == "final":
                break
        total_time = time.perf_counter() - start

        results["stt_first_result_ms"] = round(first_result * 1000, 1) if first_result else None
        results["stt_total_ms"] = round(total_time * 1000, 1)
    except Exception as e:
        results["stt_error"] = str(e)

    return results


async def benchmark_single_session():
    """Benchmark single session with all components."""
    results = {
        "single_session": {},
        "component_benchmarks": {}
    }

    # LLM benchmark
    print("Benchmarking LLM...", flush=True)
    llm_results = await benchmark_llm_latency()
    results["component_benchmarks"]["llm"] = llm_results
    if "llm_first_token_ms" in llm_results:
        results["single_session"]["llm_first_token_ms"] = llm_results["llm_first_token_ms"]
    if "llm_total_ms" in llm_results:
        results["single_session"]["llm_total_ms"] = llm_results["llm_total_ms"]

    # TTS benchmark
    print("Benchmarking TTS...", flush=True)
    tts_results = await benchmark_tts_latency()
    results["component_benchmarks"]["tts"] = tts_results
    if "tts_first_chunk_ms" in tts_results:
        results["single_session"]["tts_first_chunk_ms"] = tts_results["tts_first_chunk_ms"]
    if "tts_total_ms" in tts_results:
        results["single_session"]["tts_total_ms"] = tts_results["tts_total_ms"]

    # STT benchmark
    print("Benchmarking STT...", flush=True)
    stt_results = await benchmark_stt_latency()
    results["component_benchmarks"]["stt"] = stt_results
    if "stt_first_result_ms" in stt_results:
        results["single_session"]["stt_first_result_ms"] = stt_results["stt_first_result_ms"]
    if "stt_total_ms" in stt_results:
        results["single_session"]["stt_total_ms"] = stt_results["stt_total_ms"]

    # Calculate estimated E2E latency
    llm_ms = results["single_session"].get("llm_first_token_ms", 0)
    tts_ms = results["single_session"].get("tts_first_chunk_ms", 0)
    stt_ms = results["single_session"].get("stt_first_result_ms", 0)

    if llm_ms and tts_ms:
        results["single_session"]["e2e_estimate_ms"] = round(llm_ms + tts_ms + stt_ms, 1) if stt_ms else round(llm_ms + tts_ms, 1)

    return results


async def main():
    output = Path(".sisyphus/evidence/benchmark_results.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "environment": {
            "tts_backend": os.getenv("TTS_BACKEND", "qwen3-tts"),
            "stt_backend": os.getenv("STT_BACKEND", "paraformer-streaming"),
        }
    }

    print("Starting performance benchmark...", flush=True)
    session_results = await benchmark_single_session()
    results.update(session_results)

    # Write results
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nBenchmark results saved to: {output}")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

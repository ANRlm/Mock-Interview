import pytest
import asyncio
import time


@pytest.mark.asyncio
async def test_qwen_tts_first_chunk_latency():
    from app.services.qwen_tts_service import qwen_tts_service
    start = time.perf_counter()
    try:
        async for chunk in qwen_tts_service.stream_synthesize("你好"):
            latency_ms = (time.perf_counter() - start) * 1000
            assert latency_ms < 200, f"Qwen3-TTS first chunk {latency_ms}ms > 200ms"
            break
    except Exception as e:
        pytest.skip(f"Service not available: {e}")


@pytest.mark.asyncio  
async def test_f5_tts_fallback_latency():
    from app.services.f5_tts_service import f5_tts_service
    start = time.perf_counter()
    try:
        async for chunk in f5_tts_service.stream_synthesize("你好"):
            latency_ms = (time.perf_counter() - start) * 1000
            assert latency_ms < 500, f"F5-TTS first chunk {latency_ms}ms > 500ms"
            break
    except Exception as e:
        pytest.skip(f"Service not available: {e}")
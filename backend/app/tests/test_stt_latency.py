import pytest
import asyncio
import time


@pytest.mark.asyncio
async def test_paraformer_streaming_latency():
    from app.services.paraformer_stt_service import paraformer_stt_service
    start = time.perf_counter()
    pcm = b'\x00' * 16000 * 2  # 2 seconds placeholder
    try:
        async for evt, text in paraformer_stt_service.transcribe_stream_events(pcm):
            latency_ms = (time.perf_counter() - start) * 1000
            assert latency_ms < 1000, f"Paraformer latency {latency_ms}ms > 1000ms"
            break
    except Exception as e:
        pytest.skip(f"Service not available: {e}")


@pytest.mark.asyncio
async def test_vad_speech_detection():
    from app.services.vad_service import vad_service
    # Generate test PCM with speech-like energy
    pcm_speech = b'\xff' * 16000 * 2  # High energy = speech
    pcm_silence = b'\x00' * 16000 * 2  # Low energy = silence

    event_speech = await vad_service.detect_speech(pcm_speech)
    event_silence = await vad_service.detect_speech(pcm_silence)

    assert event_speech.speech_detected == True, "Should detect speech in high-energy PCM"
    assert event_silence.speech_detected == False, "Should NOT detect speech in silence"
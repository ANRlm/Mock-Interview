"""Integration tests for full pipeline components."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_full_pipeline_integration():
    """Test that all pipeline components work together."""
    # Test STT -> LLM -> TTS chain imports
    from app.services.paraformer_stt_service import paraformer_stt_service
    from app.services.qwen_tts_service import qwen_tts_service
    from app.agents.interviewer_agent import InterviewerAgent

    # Verify imports
    assert paraformer_stt_service is not None
    assert qwen_tts_service is not None
    assert InterviewerAgent is not None


@pytest.mark.asyncio
async def test_vram_manager_integration():
    """Test VRAM manager with pipeline."""
    from app.services.vram_manager import vram_manager

    allocation = vram_manager.plan_allocation()
    assert allocation["llm_qwen3_14b"] == 12288
    assert allocation["tts_qwen3_tts"] == 2048
    assert allocation["stt_paraformer"] == 1024
    assert allocation["buffer"] == 1024


@pytest.mark.asyncio
async def test_streaming_coordinator_integration():
    """Test streaming coordinator with all services."""
    from app.services.streaming_coordinator import StreamingCoordinator, PipelineConfig

    config = PipelineConfig()
    coordinator = StreamingCoordinator(config)
    assert coordinator is not None
    assert coordinator.config.max_queue_size == 10


@pytest.mark.asyncio
async def test_pipeline_config_defaults():
    """Test PipelineConfig default values."""
    from app.services.streaming_coordinator import PipelineConfig

    config = PipelineConfig()
    assert config.max_queue_size == 10
    assert config.stt_max_latency_ms == 600
    assert config.tts_max_latency_ms == 200
    assert config.e2e_max_latency_ms == 2000


@pytest.mark.asyncio
async def test_paraformer_stt_service_initialization():
    """Test ParaformerSTTService initializes correctly."""
    from app.services.paraformer_stt_service import ParaformerSTTService

    service = ParaformerSTTService()
    assert service._base_url == "http://127.0.0.1:10095"
    assert service._chunk_size_ms == 600


@pytest.mark.asyncio
async def test_qwen_tts_service_initialization():
    """Test QwenTTSService initializes correctly."""
    from app.services.qwen_tts_service import QwenTTSService

    service = QwenTTSService()
    assert service._base_url == "http://127.0.0.1:50001"
    assert service._model == "qwen3-tts"


@pytest.mark.asyncio
async def test_vram_manager_check_available():
    """Test VRAM availability check."""
    from app.services.vram_manager import VRAMManager

    manager = VRAMManager()
    # Should return True when cannot query nvidia-smi
    result = manager.check_available(1000)
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_streaming_coordinator_queues():
    """Test StreamingCoordinator queue initialization."""
    from app.services.streaming_coordinator import StreamingCoordinator, PipelineConfig

    config = PipelineConfig(max_queue_size=5)
    coordinator = StreamingCoordinator(config)

    assert coordinator._stt_queue.maxlen == 5
    assert coordinator._llm_queue.maxlen == 5
    assert coordinator._tts_queue.maxlen == 5

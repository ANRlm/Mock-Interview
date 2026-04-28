"""Unit tests for FasterWhisperSTTService - CUDA-accelerated STT."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np


class TestFasterWhisperSTTServiceInit:
    """Tests for FasterWhisperSTTService initialization."""

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_init_default_params(self, mock_whisper_model):
        """Test initialization with default parameters."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()

        assert service._model_size == "large-v3"
        assert service._device == "cuda"
        assert service._compute_type == "float16"
        assert service._model is None

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_init_custom_params(self, mock_whisper_model):
        """Test initialization with custom parameters."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService(
            model_size="base",
            device="cpu",
            compute_type="int8",
        )

        assert service._model_size == "base"
        assert service._device == "cpu"
        assert service._compute_type == "int8"

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_init_stores_model_not_loaded(self, mock_whisper_model):
        """Test that model is not loaded until ensure_model_ready is called."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()
        assert service._model is None


class TestFasterWhisperSTTServiceEnsureReady:
    """Tests for ensure_model_ready method."""

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    @pytest.mark.asyncio
    async def test_ensure_ready_loads_model(self, mock_whisper_model):
        """Test that ensure_model_ready loads the model."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        service = FasterWhisperSTTService()
        result = await service.ensure_model_ready()

        assert result is True
        mock_whisper_model.assert_called_once_with(
            "large-v3",
            device="cuda",
            compute_type="float16",
            download_root="~/.cache/whisper",
        )

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    @pytest.mark.asyncio
    async def test_ensure_ready_returns_true_when_already_loaded(self, mock_whisper_model):
        """Test ensure_model_ready returns True if model already loaded."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        mock_model_instance = MagicMock()
        service = FasterWhisperSTTService()
        service._model = mock_model_instance

        result = await service.ensure_model_ready()

        assert result is True
        mock_whisper_model.assert_not_called()

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    @pytest.mark.asyncio
    async def test_ensure_ready_handles_load_error(self, mock_whisper_model):
        """Test ensure_model_ready handles loading errors gracefully."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        mock_whisper_model.side_effect = RuntimeError("CUDA out of memory")

        service = FasterWhisperSTTService()
        result = await service.ensure_model_ready()

        assert result is False


class TestFasterWhisperSTTServiceTranscribe:
    """Tests for transcription functionality."""

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    @pytest.mark.asyncio
    async def test_transcribe_streaming_empty_bytes(self, mock_whisper_model):
        """Test transcribe_streaming with empty audio returns early."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()
        partials, final_text = await service.transcribe_streaming(b"")

        assert partials == []
        assert final_text == ""

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    @pytest.mark.asyncio
    async def test_transcribe_streaming_loads_model_if_needed(self, mock_whisper_model):
        """Test that transcription loads model if not already loaded."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        # Mock segments
        mock_segment = MagicMock()
        mock_segment.text = "测试文本"
        mock_segment.words = None
        mock_model_instance.transcribe.return_value = (
            [mock_segment],
            MagicMock(language="zh"),
        )

        service = FasterWhisperSTTService()
        # Model not loaded yet
        assert service._model is None

        # Create valid PCM audio (16000Hz, 1 second = 32000 bytes)
        pcm_bytes = b"\x00\x00" * 16000

        partials, final_text = await service.transcribe_streaming(pcm_bytes)

        # Should have triggered model loading
        mock_whisper_model.assert_called_once()

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    @pytest.mark.asyncio
    async def test_transcribe_streaming_raises_on_empty_result(self, mock_whisper_model):
        """Test transcribe_streaming raises error when no transcription returned."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        # Return empty segments
        mock_model_instance.transcribe.return_value = ([], MagicMock(language="zh"))

        service = FasterWhisperSTTService()
        service._model = mock_model_instance

        pcm_bytes = b"\x00\x00" * 16000

        with pytest.raises(RuntimeError, match="stt_transcription_empty"):
            await service.transcribe_streaming(pcm_bytes)


class TestFasterWhisperSTTServiceNormalization:
    """Tests for PCM normalization methods."""

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_normalize_pcm16_mono_odd_length(self, mock_whisper_model):
        """Test that odd-length PCM is handled by trimming last byte."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()
        # Odd-length PCM
        pcm = b"\x00\x01\x02"
        result = service._normalize_pcm16_mono(
            pcm_bytes=pcm,
            source_rate=16000,
            target_rate=16000,
        )
        # Should trim to even length
        assert len(result) == 2

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_normalize_pcm16_mono_invalid_sample_rate(self, mock_whisper_model):
        """Test that invalid sample rate raises error."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()
        with pytest.raises(RuntimeError, match="invalid_sample_rate"):
            service._normalize_pcm16_mono(
                pcm_bytes=b"\x00\x00",
                source_rate=0,
                target_rate=16000,
            )

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_pcm16_to_float32_conversion(self, mock_whisper_model):
        """Test PCM16 to float32 conversion produces correct range."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()
        # PCM16: max positive value
        pcm = b"\xff\x7f"  # 32767 in little-endian
        result = service._pcm16_to_float32(pcm)

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        # Should be normalized to [-1, 1]
        assert np.allclose(result[0], 1.0, atol=0.01)


class TestFasterWhisperSTTServiceBuildPartial:
    """Tests for _build_partials helper method."""

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_build_partials_removes_duplicates(self, mock_whisper_model):
        """Test that _build_partials removes consecutive duplicates."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()
        result = service._build_partials(["hello", "hello", "world"], "hello world")

        assert result == ["hello", "world", "hello world"]

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_build_partials_empty_online_texts(self, mock_whisper_model):
        """Test _build_partials handles empty online texts."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()
        result = service._build_partials([], "final answer")

        assert result == ["final answer"]

    @patch("app.services.faster_whisper_stt_service.WhisperModel")
    def test_build_partials_short_final_text(self, mock_whisper_model):
        """Test _build_partials handles short final text."""
        from app.services.faster_whisper_stt_service import FasterWhisperSTTService

        service = FasterWhisperSTTService()
        result = service._build_partials(["hi"], "hi")

        assert result == ["hi"]

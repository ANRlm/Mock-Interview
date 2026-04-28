"""Unit tests for CoquiXTTSService - CUDA-accelerated TTS."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path


class TestCoquiXTTSServiceInit:
    """Tests for CoquiXTTSService initialization."""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_init_default_params(self, mock_path, mock_tts):
        """Test initialization with default parameters."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()

        assert service._model_path is None
        assert service._device == "cuda"
        assert service._output_sample_rate == 24000
        assert service._tts is None
        assert service._model_loaded is False
        mock_cache_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_init_custom_params(self, mock_path, mock_tts):
        """Test initialization with custom parameters."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService(
            model_path="xtts_v2",
            device="cpu",
            output_sample_rate=22050,
        )

        assert service._model_path == "xtts_v2"
        assert service._device == "cpu"
        assert service._output_sample_rate == 22050

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_init_creates_cache_dir(self, mock_path, mock_tts):
        """Test initialization creates cache directory."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()

        mock_path.assert_called()
        mock_cache_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_init_stores_model_not_loaded(self, mock_path, mock_tts):
        """Test that model is not loaded until ensure_ready is called."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()
        assert service._tts is None
        assert service._model_loaded is False


class TestCoquiXTTSServiceEnsureReady:
    """Tests for ensure_ready method."""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_ensure_ready_loads_model(self, mock_path, mock_tts):
        """Test that ensure_ready loads the TTS model."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        mock_tts_instance = MagicMock()
        mock_tts.return_value = mock_tts_instance

        service = CoquiXTTSService()
        result = await service.ensure_ready()

        assert result is True
        assert service._model_loaded is True
        assert service._tts is not None

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_ensure_ready_idempotent(self, mock_path, mock_tts):
        """Test that ensure_ready is idempotent (doesn't reload)."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        mock_tts_instance = MagicMock()
        mock_tts.return_value = mock_tts_instance

        service = CoquiXTTSService()
        await service.ensure_ready()
        result2 = await service.ensure_ready()

        assert result2 is True
        # TTS should only be instantiated once
        assert mock_tts.call_count == 1

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_ensure_ready_returns_false_on_error(self, mock_path, mock_tts):
        """Test ensure_ready handles loading errors gracefully."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        mock_tts.side_effect = RuntimeError("CUDA out of memory")

        service = CoquiXTTSService()
        result = await service.ensure_ready()

        assert result is False


class TestCoquiXTTSServiceSynthesize:
    """Tests for synthesis functionality."""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self, mock_path, mock_tts):
        """Test synthesize with empty text returns empty result."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()
        pcm_bytes, fmt = await service.synthesize("")

        assert pcm_bytes == b""
        assert fmt == "pcm"

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_synthesize_whitespace_text(self, mock_path, mock_tts):
        """Test synthesize with whitespace-only text returns empty result."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()
        pcm_bytes, fmt = await service.synthesize("   \n\t  ")

        assert pcm_bytes == b""
        assert fmt == "pcm"

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_synthesize_returns_pcm_format(self, mock_path, mock_tts):
        """Test synthesize returns PCM bytes and format string."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        mock_tts_instance = MagicMock()
        mock_tts_instance.tts.return_value = [0.0] * 24000  # 1 second of audio
        mock_tts.return_value = mock_tts_instance

        service = CoquiXTTSService()
        # Patch cache path to not exist
        mock_cache_dir.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=False)))

        pcm_bytes, fmt = await service.synthesize("测试")

        assert fmt == "pcm"
        assert isinstance(pcm_bytes, bytes)


class TestCoquiXTTSServiceStreamSynthesize:
    """Tests for stream_synthesize method."""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_stream_synthesize_empty_text(self, mock_path, mock_tts):
        """Test stream_synthesize with empty text returns early."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()
        chunks = []
        async for chunk in service.stream_synthesize(""):
            chunks.append(chunk)

        assert chunks == []

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_stream_synthesize_cache_hit(self, mock_path, mock_tts):
        """Test stream_synthesize uses cache when available."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        # Mock cache path that exists
        mock_cache_path = MagicMock()
        mock_cache_path.exists.return_value = True
        mock_cache_path.read_bytes.return_value = b"cached_audio_data"
        mock_cache_dir.__truediv__ = MagicMock(return_value=mock_cache_path)

        service = CoquiXTTSService()
        chunks = []
        async for chunk in service.stream_synthesize("测试文本"):
            chunks.append(chunk)

        # Should have read from cache
        mock_cache_path.read_bytes.assert_called_once()
        assert b"cached_audio_data" in chunks

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    @pytest.mark.asyncio
    async def test_stream_synthesize_cache_miss(self, mock_path, mock_tts):
        """Test stream_synthesize generates audio on cache miss."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        # Mock cache path that does not exist
        mock_cache_path = MagicMock()
        mock_cache_path.exists.return_value = False
        mock_cache_dir.__truediv__ = MagicMock(return_value=mock_cache_path)

        mock_tts_instance = MagicMock()
        mock_tts_instance.tts.return_value = [0.0] * 24000  # 1 second of audio
        mock_tts.return_value = mock_tts_instance

        service = CoquiXTTSService()
        service._tts = mock_tts_instance
        service._model_loaded = True

        chunks = []
        async for chunk in service.stream_synthesize("测试"):
            chunks.append(chunk)

        # Should have generated audio
        mock_tts_instance.tts.assert_called_once()
        assert len(chunks) > 0


class TestCoquiXTTSServiceCacheKey:
    """Tests for _cache_key method."""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_cache_key_deterministic(self, mock_path, mock_tts):
        """Test that _cache_key produces consistent results."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()
        key1 = service._cache_key("测试文本")
        key2 = service._cache_key("测试文本")

        assert key1 == key2

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_cache_key_different_for_different_text(self, mock_path, mock_tts):
        """Test that different text produces different cache keys."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()
        key1 = service._cache_key("文本1")
        key2 = service._cache_key("文本2")

        assert key1 != key2


class TestCoquiXTTSServiceProperties:
    """Tests for service properties."""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_is_ready_property(self, mock_path, mock_tts):
        """Test is_ready property reflects model state."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()
        assert service.is_ready is False

        service._model_loaded = True
        service._tts = MagicMock()
        assert service.is_ready is True

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_sample_rate_property(self, mock_path, mock_tts):
        """Test sample_rate property returns configured value."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService(output_sample_rate=22050)
        assert service.sample_rate == 22050


class TestCoquiXTTSServiceSynthesizePCM:
    """Tests for _synthesize_pcm method."""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_synthesize_pcm_raises_when_not_initialized(self, mock_path, mock_tts):
        """Test _synthesize_pcm raises error when TTS not initialized."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        service = CoquiXTTSService()
        # TTS is None

        with pytest.raises(RuntimeError, match="TTS model not initialized"):
            service._synthesize_pcm("测试")

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_synthesize_pcm_returns_empty_on_none_wav(self, mock_path, mock_tts):
        """Test _synthesize_pcm handles None wav response."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        mock_tts_instance = MagicMock()
        mock_tts_instance.tts.return_value = None
        mock_tts.return_value = mock_tts_instance

        service = CoquiXTTSService()
        service._tts = mock_tts_instance

        result = service._synthesize_pcm("测试")

        assert result == b""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_synthesize_pcm_returns_empty_on_empty_wav(self, mock_path, mock_tts):
        """Test _synthesize_pcm handles empty wav response."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        mock_tts_instance = MagicMock()
        mock_tts_instance.tts.return_value = []
        mock_tts.return_value = mock_tts_instance

        service = CoquiXTTSService()
        service._tts = mock_tts_instance

        result = service._synthesize_pcm("测试")

        assert result == b""

    @patch("app.services.coqui_xtts_service.TTS")
    @patch("app.services.coqui_xtts_service.Path")
    def test_synthesize_pcm_converts_to_int16(self, mock_path, mock_tts):
        """Test _synthesize_pcm converts float audio to int16 PCM."""
        from app.services.coqui_xtts_service import CoquiXTTSService

        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir

        mock_tts_instance = MagicMock()
        # 1 second of 24kHz audio at 0.5 amplitude
        mock_tts_instance.tts.return_value = [0.5] * 24000
        mock_tts.return_value = mock_tts_instance

        service = CoquiXTTSService()
        service._tts = mock_tts_instance

        result = service._synthesize_pcm("测试")

        # Should be 16-bit PCM, 2 bytes per sample
        assert len(result) == 24000 * 2
        # First two bytes should represent 0.5 * 32767 = 16383
        import struct
        first_sample = struct.unpack("<h", result[:2])[0]
        assert first_sample == 16383

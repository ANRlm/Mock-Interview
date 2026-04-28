"""Unit tests for LlamaCppLLMService - CUDA-accelerated LLM."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestLlamaCppLLMServiceInit:
    """Tests for LlamaCppLLMService initialization."""

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_init_default_params(self, mock_llama):
        """Test initialization with default parameters."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()

        assert service.model_path == "/models/qwen3-8b.Q4_K_M.gguf"
        assert service.n_ctx == 8192
        assert service.n_gpu_layers == 35
        assert service.n_threads == 8
        assert service.n_batch == 512
        assert service._model is None

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_init_custom_params(self, mock_llama):
        """Test initialization with custom parameters."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService(
            model_path="/custom/path/model.gguf",
            n_ctx=4096,
            n_gpu_layers=20,
            n_threads=4,
            n_batch=256,
        )

        assert service.model_path == "/custom/path/model.gguf"
        assert service.n_ctx == 4096
        assert service.n_gpu_layers == 20
        assert service.n_threads == 4
        assert service.n_batch == 256

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_init_stores_model_not_loaded(self, mock_llama):
        """Test that model is not loaded until ensure_ready is called."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()
        assert service._model is None
        assert service._lock is not None


class TestLlamaCppLLMServiceEnsureReady:
    """Tests for ensure_ready method."""

    @patch("app.services.llama_cpp_llm_service.Llama")
    @pytest.mark.asyncio
    async def test_ensure_ready_loads_model(self, mock_llama):
        """Test that ensure_ready loads the model."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        mock_model_instance = MagicMock()
        mock_llama.return_value = mock_model_instance

        service = LlamaCppLLMService()
        await service.ensure_ready()

        mock_llama.assert_called_once_with(
            model_path="/models/qwen3-8b.Q4_K_M.gguf",
            n_ctx=8192,
            n_gpu_layers=35,
            n_threads=8,
            n_batch=512,
            use_mmap=True,
            use_mlock=False,
            flash_attention=True,
            verbose=False,
        )

    @patch("app.services.llama_cpp_llm_service.Llama")
    @pytest.mark.asyncio
    async def test_ensure_ready_idempotent(self, mock_llama):
        """Test that ensure_ready is idempotent (doesn't reload)."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        mock_model_instance = MagicMock()
        mock_llama.return_value = mock_model_instance

        service = LlamaCppLLMService()
        await service.ensure_ready()
        await service.ensure_ready()

        # Should only be called once
        assert mock_llama.call_count == 1

    @patch("app.services.llama_cpp_llm_service.Llama")
    @pytest.mark.asyncio
    async def test_ensure_ready_thread_safe(self, mock_llama):
        """Test that ensure_ready handles concurrent calls safely."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        mock_model_instance = MagicMock()
        mock_llama.return_value = mock_model_instance

        service = LlamaCppLLMService()

        # Call ensure_ready multiple times concurrently
        await service.ensure_ready()
        await service.ensure_ready()

        # Should not raise and model should be loaded once
        assert service._model is not None


class TestLlamaCppLLMServiceBuildPrompt:
    """Tests for _build_prompt method."""

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_build_prompt_system_message(self, mock_llama):
        """Test _build_prompt formats system messages correctly."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()
        messages = [{"role": "system", "content": "You are helpful."}]
        result = service._build_prompt(messages)

        assert "<|im_start|>system\nYou are helpful.<|im_end|>" in result
        assert "<|im_start|>assistant\n" in result

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_build_prompt_user_message(self, mock_llama):
        """Test _build_prompt formats user messages correctly."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()
        messages = [{"role": "user", "content": "Hello!"}]
        result = service._build_prompt(messages)

        assert "<|im_start|>user\nHello!<|im_end|>" in result
        assert "<|im_start|>assistant\n" in result

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_build_prompt_assistant_message(self, mock_llama):
        """Test _build_prompt formats assistant messages correctly."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()
        messages = [{"role": "assistant", "content": "I am here to help."}]
        result = service._build_prompt(messages)

        assert "<|im_start|>assistant\nI am here to help.<|im_end|>" in result

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_build_prompt_multiple_messages(self, mock_llama):
        """Test _build_prompt handles conversation history."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi!"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"},
        ]
        result = service._build_prompt(messages)

        assert "<|im_start|>system" in result
        assert "<|im_start|>user" in result
        assert "<|im_start|>assistant" in result
        # Should end with assistant prompt
        assert result.endswith("<|im_start|>assistant\n")

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_build_prompt_empty_content(self, mock_llama):
        """Test _build_prompt handles empty content gracefully."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()
        messages = [{"role": "user", "content": ""}]
        result = service._build_prompt(messages)

        assert "<|im_start|>user\n<|im_end|>" in result


class TestLlamaCppLLMServiceChat:
    """Tests for chat method."""

    @patch("app.services.llama_cpp_llm_service.Llama")
    @pytest.mark.asyncio
    async def test_chat_non_streaming(self, mock_llama):
        """Test non-streaming chat returns complete response."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        mock_model_instance = MagicMock()
        mock_model_instance.return_value = {"choices": [{"text": "Test response"}]}
        mock_llama.return_value = mock_model_instance

        service = LlamaCppLLMService()
        await service.ensure_ready()

        messages = [{"role": "user", "content": "Hello"}]
        result = await service.chat(messages, stream=False)

        assert result == "Test response"

    @patch("app.services.llama_cpp_llm_service.Llama")
    @pytest.mark.asyncio
    async def test_chat_streaming_returns_iterator(self, mock_llama):
        """Test streaming chat returns an async iterator."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        mock_model_instance = MagicMock()
        mock_llama.return_value = mock_model_instance

        service = LlamaCppLLMService()
        await service.ensure_ready()

        messages = [{"role": "user", "content": "Hello"}]
        result = service.chat(messages, stream=True)

        # Should return an async iterator
        import collections.abc
        assert isinstance(result, collections.abc.AsyncIterator)

    @patch("app.services.llama_cpp_llm_service.Llama")
    @pytest.mark.asyncio
    async def test_chat_without_ensure_ready_raises(self, mock_llama):
        """Test that chat raises error if ensure_ready was not called."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()
        # Model not loaded
        assert service._model is None

        messages = [{"role": "user", "content": "Hello"}]

        # Non-streaming should raise
        with pytest.raises(RuntimeError, match="Model not loaded"):
            await service.chat(messages, stream=False)


class TestLlamaCppLLMServiceGenerate:
    """Tests for internal generation methods."""

    @patch("app.services.llama_cpp_llm_service.Llama")
    @pytest.mark.asyncio
    async def test_generate_sync_raises_when_model_not_loaded(self, mock_llama):
        """Test _generate raises error when model not loaded."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()

        with pytest.raises(RuntimeError, match="Model not loaded"):
            await service._generate("test prompt", 0.7, 100, None)

    @patch("app.services.llama_cpp_llm_service.Llama")
    @pytest.mark.asyncio
    async def test_stream_generate_raises_when_model_not_loaded(self, mock_llama):
        """Test _stream_generate raises error when model not loaded."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()

        with pytest.raises(RuntimeError, match="Model not loaded"):
            await anext(service._stream_generate("test prompt", 0.7, 100, None))


class TestLlamaCppLLMServiceTokenCount:
    """Tests for get_token_count method."""

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_get_token_count_with_loaded_model(self, mock_llama):
        """Test get_token_count uses model when available."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        mock_model_instance = MagicMock()
        mock_model_instance.n_tokens.return_value = 10
        mock_llama.return_value = mock_model_instance

        service = LlamaCppLLMService()
        service._model = mock_model_instance

        result = service.get_token_count("Hello world")

        mock_model_instance.n_tokens.assert_called_once_with("Hello world")
        assert result == 10

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_get_token_count_fallback(self, mock_llama):
        """Test get_token_count falls back to approximation."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        service = LlamaCppLLMService()
        # No model loaded
        service._model = None

        result = service.get_token_count("Hello world")

        # Should approximate: len("Hello world") / 4 = 2.75 -> 2
        assert result == 2

    @patch("app.services.llama_cpp_llm_service.Llama")
    def test_get_token_count_handles_model_error(self, mock_llama):
        """Test get_token_count handles model errors gracefully."""
        from app.services.llama_cpp_llm_service import LlamaCppLLMService

        mock_model_instance = MagicMock()
        mock_model_instance.n_tokens.side_effect = RuntimeError("Token error")
        mock_llama.return_value = mock_model_instance

        service = LlamaCppLLMService()
        service._model = mock_model_instance

        result = service.get_token_count("Hello world")

        # Should fall back to approximation
        assert result == 2

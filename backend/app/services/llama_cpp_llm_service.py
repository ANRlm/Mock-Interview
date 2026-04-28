"""CUDA-accelerated llama.cpp LLM service using Qwen2 chat format."""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from llama_cpp import Llama

logger = logging.getLogger(__name__)


class LlamaCppLLMService:
    """CUDA-accelerated llama.cpp LLM service for local inference.

    Uses Qwen2 chat format for prompt construction.
    Optimized for RTX 5080 16GB with n_gpu_layers=35.
    """

    def __init__(
        self,
        model_path: str | None = None,
        n_ctx: int = 8192,
        n_gpu_layers: int = 35,
        n_threads: int = 8,
        n_batch: int = 512,
    ) -> None:
        """Initialize the LLM service.

        Args:
            model_path: Path to the GGUF model file. If None, uses default from config.
            n_ctx: Context window size (tokens).
            n_gpu_layers: Number of layers to offload to GPU (35 for RTX 5080 16GB).
            n_threads: CPU threads for inference.
            n_batch: Batch size for prompt processing.
        """
        self.model_path = model_path or "/models/qwen3-8b.Q4_K_M.gguf"
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.n_batch = n_batch

        self._model: Llama | None = None
        self._lock = asyncio.Lock()

    async def ensure_ready(self) -> None:
        """Load the model if not already loaded (async, thread-safe)."""
        if self._model is not None:
            return

        async with self._lock:
            if self._model is not None:
                return

            logger.info(
                f"Loading llama.cpp model: {self.model_path}, "
                f"n_ctx={self.n_ctx}, n_gpu_layers={self.n_gpu_layers}"
            )

            def _load_sync() -> None:
                self._model = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    n_threads=self.n_threads,
                    n_batch=self.n_batch,
                    use_mmap=True,
                    use_mlock=False,
                    flash_attention=True,
                    verbose=False,
                )

            await asyncio.to_thread(_load_sync)
            logger.info("llama.cpp model loaded successfully")

    def _build_prompt(self, messages: list[dict[str, str]]) -> str:
        """Build a prompt string from chat messages using Qwen2 format.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Returns:
            Formatted prompt string in Qwen2 chat template format.
        """
        prompt_parts: list[str] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == "user":
                prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == "assistant":
                prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")

        prompt_parts.append("<|im_start|>assistant\n")
        return "".join(prompt_parts)

    async def _stream_generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop: list[str] | None,
    ) -> AsyncIterator[str]:
        """Internal streaming generator for token-by-token output.

        Args:
            prompt: The formatted prompt string.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences to terminate generation.

        Yields:
            Generated tokens as strings.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call ensure_ready() first.")

        stop_sequences = stop or []

        def _stream_sync() -> AsyncIterator[str]:
            def _token_callback(token: bytes) -> bool:
                """Called for each generated token. Returns False to stop."""
                return True

            try:
                for output in self._model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop_sequences,
                    stream=True,
                    stream_callback=_token_callback,
                ):
                    if isinstance(output, str):
                        yield output
                    elif hasattr(output, "choices"):
                        choice = output["choices"][0]
                        if choice.get("finish_reason") == "stop":
                            break
                        delta = choice.get("delta", {})
                        text = delta.get("content", "") or str(delta)
                        if text:
                            yield text
            except Exception as e:
                logger.error(f"Streaming generation error: {e}")
                raise

        for token in await asyncio.to_thread(_stream_sync):
            yield token

    async def _generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop: list[str] | None,
    ) -> str:
        """Internal non-streaming generation.

        Args:
            prompt: The formatted prompt string.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences to terminate generation.

        Returns:
            Complete generated response string.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call ensure_ready() first.")

        stop_sequences = stop or []

        def _generate_sync() -> str:
            try:
                output = self._model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop_sequences,
                    stream=False,
                )
                if hasattr(output, "choices"):
                    return output["choices"][0]["text"]
                return str(output)
            except Exception as e:
                logger.error(f"Non-streaming generation error: {e}")
                raise

        return await asyncio.to_thread(_generate_sync)

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: list[str] | None = None,
    ) -> AsyncIterator[str] | str:
        """Chat with the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            stream: If True, returns an async iterator of tokens.
                    If False, waits and returns complete response.
            temperature: Sampling temperature (0.0-2.0, lower = more deterministic).
            max_tokens: Maximum tokens to generate.
            stop: List of stop sequences to terminate generation.

        Returns:
            If stream=True: AsyncIterator[str] yielding tokens.
            If stream=False: Complete response string.
        """
        await self.ensure_ready()

        prompt = self._build_prompt(messages)

        if stream:
            return self._stream_generate(prompt, temperature, max_tokens, stop)
        else:
            return await self._generate(prompt, temperature, max_tokens, stop)

    def get_token_count(self, text: str) -> int:
        """Get the token count for a text string.

        Args:
            text: Input text string.

        Returns:
            Approximate token count.
        """
        if self._model is not None:
            try:
                return self._model.n_tokens(text)
            except Exception:
                pass

        approx_ratio = len(text) / 4
        return int(approx_ratio)


llama_cpp_llm_service = LlamaCppLLMService()

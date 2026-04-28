"""CUDA-accelerated llama.cpp LLM service using Qwen2 chat format."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import AsyncIterator

from app.config import get_settings
from llama_cpp import Llama

logger = logging.getLogger(__name__)

# End patterns for early stopping detection
END_PATTERNS = [
    re.compile(r"</s>"),
    re.compile(r"<\|im_end\|>"),
    re.compile(r"<end_turn>"),
    re.compile(r"^STOP$", re.MULTILINE),
]


@dataclass
class BatchedRequest:
    """A single request in the batch queue."""
    prompt: str
    temperature: float
    max_tokens: int
    stop: list[str] | None
    future: asyncio.Future[str] = field(default_factory=asyncio.Future)


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
        batch_enabled: bool = False,
        batch_max_size: int = 8,
        batch_timeout_ms: int = 100,
    ) -> None:
        """Initialize the LLM service.

        Args:
            model_path: Path to the GGUF model file. If None, uses default from config.
            n_ctx: Context window size (tokens).
            n_gpu_layers: Number of layers to offload to GPU (35 for RTX 5080 16GB).
            n_threads: CPU threads for inference.
            n_batch: Batch size for prompt processing.
            batch_enabled: Enable dynamic request batching.
            batch_max_size: Max requests per batch.
            batch_timeout_ms: Timeout in ms before processing partial batch.
        """
        self.model_path = model_path or "/models/qwen3-8b.Q4_K_M.gguf"
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.n_batch = n_batch

        # Dynamic batching settings
        self.batch_enabled = batch_enabled
        self.batch_max_size = batch_max_size
        self.batch_timeout_ms = batch_timeout_ms

        # Request queue and processing task for batching
        self._request_queue: asyncio.Queue[BatchedRequest | None] = asyncio.Queue()
        self._batch_task: asyncio.Task[None] | None = None
        self._shutdown_event = asyncio.Event()

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

        # Start batch processor if batching is enabled
        if self.batch_enabled and self._batch_task is None:
            self._shutdown_event.clear()
            self._batch_task = asyncio.create_task(self._batch_processor())
            logger.info(
                f"Batch processor started: max_size={self.batch_max_size}, "
                f"timeout={self.batch_timeout_ms}ms"
            )

    async def _batch_processor(self) -> None:
        """Process batches of requests with dynamic sizing and timeout."""
        logger.info("Batch processor task started")
        while not self._shutdown_event.is_set():
            try:
                batch: list[BatchedRequest] = []
                timeout_sec = self.batch_timeout_ms / 1000.0

                # Wait for first request
                first_req = await asyncio.wait_for(
                    self._request_queue.get(),
                    timeout=timeout_sec
                )
                batch.append(first_req)

                # Collect more requests up to max_size
                while len(batch) < self.batch_max_size:
                    try:
                        req = await asyncio.wait_for(
                            self._request_queue.get(),
                            timeout=timeout_sec
                        )
                        batch.append(req)
                    except asyncio.TimeoutError:
                        break

                if batch:
                    await self._process_batch(batch)

            except asyncio.TimeoutError:
                # No requests in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"Batch processor error: {e}", exc_info=True)
                await asyncio.sleep(0.1)

        logger.info("Batch processor task stopped")

    async def _process_batch(self, batch: list[BatchedRequest]) -> None:
        """Process a batch of requests.

        Args:
            batch: List of BatchedRequest objects to process.
        """
        if not batch:
            return

        logger.debug(f"Processing batch of {len(batch)} requests")

        # For llama.cpp, we process sequentially but can share model context
        for req in batch:
            try:
                result = await self._generate(
                    req.prompt,
                    req.temperature,
                    req.max_tokens,
                    req.stop,
                )
                if not req.future.done():
                    req.future.set_result(result)
            except Exception as e:
                logger.error(f"Request processing error: {e}", exc_info=True)
                if not req.future.done():
                    req.future.set_exception(e)

    async def _submit_batched(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop: list[str] | None,
    ) -> str:
        """Submit a request to the batch queue and wait for result.

        Args:
            prompt: The formatted prompt string.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences to terminate generation.

        Returns:
            Complete generated response string.
        """
        request = BatchedRequest(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
        )
        await self._request_queue.put(request)
        return await request.future

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

        settings = get_settings()
        tokens_generated = 0
        text_buffer = []

        def _stream_sync() -> AsyncIterator[str]:
            def _token_callback(token: bytes) -> bool:
                """Called for each generated token. Returns False to stop."""
                nonlocal tokens_generated, text_buffer
                if settings.LLM_EARLY_STOPPING_ENABLED:
                    tokens_generated += 1
                    decoded = token.decode("utf-8", errors="replace")
                    text_buffer.append(decoded)
                    if tokens_generated >= settings.LLM_EARLY_STOPPING_MIN_TOKENS:
                        accumulated = "".join(text_buffer)
                        for pattern in END_PATTERNS:
                            if pattern.search(accumulated):
                                return False
                    if tokens_generated >= settings.LLM_EARLY_STOPPING_MAX_TOKENS:
                        return False
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
                settings = get_settings()
                effective_max_tokens = (
                    settings.LLM_EARLY_STOPPING_MAX_TOKENS
                    if settings.LLM_EARLY_STOPPING_ENABLED
                    else max_tokens
                )
                output = self._model(
                    prompt,
                    max_tokens=effective_max_tokens,
                    temperature=temperature,
                    stop=stop_sequences,
                    stream=False,
                )
                text = ""
                if hasattr(output, "choices"):
                    text = output["choices"][0]["text"]
                else:
                    text = str(output)
                # Trim end patterns if early stopping enabled
                if settings.LLM_EARLY_STOPPING_ENABLED:
                    for pattern in END_PATTERNS:
                        match = pattern.search(text)
                        if match:
                            text = text[:match.start()]
                            break
                return text
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
            # Use batching for non-streaming requests when enabled
            if self.batch_enabled:
                return await self._submit_batched(prompt, temperature, max_tokens, stop)
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

    async def shutdown(self) -> None:
        """Gracefully shutdown the batch processor."""
        if self._batch_task is not None:
            self._shutdown_event.set()
            self._request_queue.put_nowait(None)  # Sentinel to unblock queue
            await asyncio.gather(self._batch_task, return_exceptions=True)
            self._batch_task = None
            logger.info("Batch processor shutdown complete")


def create_llama_cpp_llm_service(
    batch_enabled: bool = False,
    batch_max_size: int = 8,
    batch_timeout_ms: int = 100,
) -> LlamaCppLLMService:
    """Factory function to create LLM service with batching config.

    Args:
        batch_enabled: Enable dynamic request batching.
        batch_max_size: Max requests per batch.
        batch_timeout_ms: Timeout in ms before processing partial batch.

    Returns:
        Configured LlamaCppLLMService instance.
    """
    return LlamaCppLLMService(
        batch_enabled=batch_enabled,
        batch_max_size=batch_max_size,
        batch_timeout_ms=batch_timeout_ms,
    )


# Singleton instance - imported by other modules
llama_cpp_llm_service = LlamaCppLLMService()
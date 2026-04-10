from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urlparse

import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.llm_profile_service import LLMProfile, llm_profile_service


class BaseAgent:
    SYSTEM_PROMPT = ""

    def __init__(self) -> None:
        self._profile: LLMProfile | None = None
        self.client: AsyncOpenAI | None = None
        self.model = settings.LLM_MODEL
        self._use_ollama_native = False
        self._last_stream_stats: dict[str, Any] = {}

    @property
    def using_ollama_native(self) -> bool:
        return self._use_ollama_native

    @property
    def active_profile_name(self) -> str:
        if self._profile is None:
            return "local"
        return self._profile.name

    def pop_last_stream_stats(self) -> dict[str, Any]:
        stats = self._last_stream_stats
        self._last_stream_stats = {}
        return stats

    async def chat(
        self, messages: list[dict[str, str]], stream: bool = True
    ) -> str | AsyncIterator[str]:
        self._last_stream_stats = {}
        await self._ensure_runtime_client()

        if self._use_ollama_native:
            if stream:
                return self._stream_chat_ollama(messages)
            return await self._chat_ollama(messages)

        if stream:
            return self._stream_chat(messages)

        extra_body = self._extra_body()
        if self.client is None:
            raise RuntimeError("LLM client not initialized")
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False,
            temperature=0.7,
            extra_body=extra_body,
        )
        message = completion.choices[0].message
        content = message.content or ""
        if isinstance(content, list):
            content = "".join(
                str(item.get("text", "")) if isinstance(item, dict) else str(item)
                for item in content
            )
        return content

    async def _stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        extra_body = self._extra_body()
        if self.client is None:
            raise RuntimeError("LLM client not initialized")
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            "temperature": 0.7,
            "extra_body": extra_body,
        }

        try:
            stream = await self.client.chat.completions.create(**kwargs)
        except Exception:
            fallback_kwargs = dict(kwargs)
            fallback_kwargs.pop("stream_options", None)
            stream = await self.client.chat.completions.create(**fallback_kwargs)
        finish_reason: str | None = None
        prompt_tokens: int | None = None
        completion_tokens: int | None = None
        async for chunk in stream:
            if chunk.choices:
                choice = chunk.choices[0]
                delta = choice.delta
                token = delta.content
                if token:
                    yield token
                if choice.finish_reason:
                    finish_reason = choice.finish_reason

            usage = chunk.usage
            if usage is not None:
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens

        stats: dict[str, Any] = {}
        if finish_reason:
            stats["done_reason"] = finish_reason
        if prompt_tokens is not None:
            stats["prompt_eval_count"] = prompt_tokens
        if completion_tokens is not None:
            stats["eval_count"] = completion_tokens

        self._last_stream_stats = stats

    async def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        await self._ensure_runtime_client()
        if self._use_ollama_native:
            return await self._chat_json_ollama(messages)

        extra_body = self._extra_body()
        if self.client is None:
            raise RuntimeError("LLM client not initialized")
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False,
            response_format={"type": "json_object"},
            temperature=0.2,
            extra_body=extra_body,
        )
        message = completion.choices[0].message
        content = message.content or "{}"
        if isinstance(content, list):
            content = "".join(
                str(item.get("text", "")) if isinstance(item, dict) else str(item)
                for item in content
            )
        if not content:
            content = "{}"
        return json.loads(content)

    def _extra_body(self) -> dict[str, Any]:
        if self._disable_thinking():
            return {"think": False}
        return {}

    def _disable_thinking(self) -> bool:
        if self._profile is not None:
            return bool(self._profile.disable_thinking)
        return bool(settings.LLM_DISABLE_THINKING)

    async def _ensure_runtime_client(self) -> None:
        async with AsyncSessionLocal() as db:
            profile = await llm_profile_service.get_runtime_profile(db)

        if self._profile == profile and self.client is not None:
            return

        self._profile = profile
        self.model = profile.model
        self.client = AsyncOpenAI(
            base_url=profile.base_url,
            api_key=profile.api_key,
            timeout=float(profile.timeout_seconds),
        )
        self._use_ollama_native = self._is_local_ollama_base()

    def _is_local_ollama_base(self) -> bool:
        base_url = (
            self._profile.base_url
            if self._profile is not None
            else settings.LLM_BASE_URL
        )
        parsed = urlparse(base_url)
        host = (parsed.hostname or "").lower()
        if host not in {
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "host.docker.internal",
            "ollama",
        }:
            return False

        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80
        return port == 11434

    def _ollama_root_url(self) -> str:
        base_url = (
            self._profile.base_url
            if self._profile is not None
            else settings.LLM_BASE_URL
        )
        base = base_url.rstrip("/")
        if base.endswith("/v1"):
            return base[:-3]
        return base

    async def _chat_ollama(self, messages: list[dict[str, str]]) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if self._disable_thinking():
            payload["think"] = False

        async with httpx.AsyncClient(
            timeout=float(
                self._profile.timeout_seconds
                if self._profile
                else settings.LLM_TIMEOUT_SECONDS
            )
        ) as client:
            response = await client.post(
                f"{self._ollama_root_url()}/api/chat", json=payload
            )
            response.raise_for_status()
            data = response.json()

        message = data.get("message") if isinstance(data, dict) else None
        content = (message or {}).get("content") if isinstance(message, dict) else ""
        if isinstance(content, str):
            return content
        return ""

    async def _chat_json_ollama(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
        }
        if self._disable_thinking():
            payload["think"] = False

        async with httpx.AsyncClient(
            timeout=float(
                self._profile.timeout_seconds
                if self._profile
                else settings.LLM_TIMEOUT_SECONDS
            )
        ) as client:
            response = await client.post(
                f"{self._ollama_root_url()}/api/chat", json=payload
            )
            response.raise_for_status()
            data = response.json()

        message = data.get("message") if isinstance(data, dict) else None
        content = (message or {}).get("content") if isinstance(message, dict) else "{}"
        if not isinstance(content, str) or not content.strip():
            return {}
        return json.loads(content)

    async def _stream_chat_ollama(
        self, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if self._disable_thinking():
            payload["think"] = False

        done_stats: dict[str, Any] = {}
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self._ollama_root_url()}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message = data.get("message") if isinstance(data, dict) else None
                    token = (
                        (message or {}).get("content")
                        if isinstance(message, dict)
                        else ""
                    )
                    if token:
                        yield token

                    if data.get("done"):
                        done_stats = {
                            "done_reason": data.get("done_reason"),
                            "prompt_eval_count": data.get("prompt_eval_count"),
                            "prompt_eval_duration": data.get("prompt_eval_duration"),
                            "eval_count": data.get("eval_count"),
                            "eval_duration": data.get("eval_duration"),
                            "load_duration": data.get("load_duration"),
                            "total_duration": data.get("total_duration"),
                        }
                        break

        self._last_stream_stats = {k: v for k, v in done_stats.items() if v is not None}

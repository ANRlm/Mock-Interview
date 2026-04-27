from typing import AsyncIterator
import httpx


class QwenTTSService:
    def __init__(self, base_url: str = "http://127.0.0.1:50001", model: str = "qwen3-tts"):
        self._base_url = base_url
        self._model = model

    async def stream_synthesize(self, text: str) -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                'POST',
                f'{self._base_url}/v1/tts',
                json={'text': text, 'model': self._model},
                headers={'Content-Type': 'application/json'}
            ) as resp:
                async for chunk in resp.aiter_bytes(chunk_size=1024):
                    if chunk:
                        yield chunk


qwen_tts_service = QwenTTSService()
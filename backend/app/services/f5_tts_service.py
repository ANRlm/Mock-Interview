from typing import AsyncIterator
import httpx


class F5TTSService:
    def __init__(self, base_url: str = "http://127.0.0.1:50001"):
        self._base_url = base_url

    async def stream_synthesize(self, text: str) -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                'POST',
                f'{self._base_url}/v1/tts',
                json={'text': text, 'model': 'f5-tts'},
                headers={'Content-Type': 'application/json'}
            ) as resp:
                async for chunk in resp.aiter_bytes(chunk_size=1024):
                    if chunk:
                        yield chunk


f5_tts_service = F5TTSService()
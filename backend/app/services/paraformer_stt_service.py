from typing import AsyncIterator, Tuple
import httpx


class ParaformerSTTService:
    def __init__(self, base_url: str = "http://127.0.0.1:10095"):
        self._base_url = base_url
        self._chunk_size_ms = 600

    async def transcribe_streaming(self, pcm_chunk: bytes) -> AsyncIterator[Tuple[str, str]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f'{self._base_url}/asr',
                    files={'audio': ('pcm', pcm_chunk, 'audio/pcm')},
                    data={'model': 'paraformer-zh-streaming'}
                )
                if resp.status_code == 200:
                    result = resp.json()
                    text = result.get('text', '')
                    yield ('final', text)
                else:
                    yield ('final', '')
            except Exception:
                yield ('final', '')

    async def transcribe_stream_events(self, pcm_chunk: bytes) -> AsyncIterator[Tuple[str, str]]:
        async for result in self.transcribe_streaming(pcm_chunk):
            yield result


paraformer_stt_service = ParaformerSTTService()
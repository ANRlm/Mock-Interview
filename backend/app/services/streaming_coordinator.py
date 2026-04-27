import asyncio
from typing import AsyncIterator, Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class PipelineConfig:
    max_queue_size: int = 10
    stt_max_latency_ms: int = 600
    tts_max_latency_ms: int = 200
    e2e_max_latency_ms: int = 2000


class StreamingCoordinator:
    def __init__(self, config: PipelineConfig = PipelineConfig()):
        self.config = config
        self._stt_queue: deque = deque(maxlen=config.max_queue_size)
        self._llm_queue: deque = deque(maxlen=config.max_queue_size)
        self._tts_queue: deque = deque(maxlen=config.max_queue_size)
        self._cancel_event: Optional[asyncio.Event] = None

    async def process_full_duplex(self, audio_chunk: bytes) -> AsyncIterator[bytes]:
        """Parallel STT→LLM→TTS processing using queue-based coordination."""
        self._cancel_event = asyncio.Event()
        tts_queue: asyncio.Queue[bytes] = asyncio.Queue(maxlen=self.config.max_queue_size)

        async def stt_wrapper():
            async for text in self._process_stt(audio_chunk):
                if self._cancel_event.is_set():
                    break
                self._llm_queue.append(text)

        async def llm_wrapper():
            while not self._cancel_event.is_set():
                if self._llm_queue:
                    text = self._llm_queue.popleft()
                    messages = [{"role": "user", "content": text}]
                    async for chunk in self._process_llm(messages):
                        if self._cancel_event.is_set():
                            break
                        await tts_queue.put(chunk)
                else:
                    await asyncio.sleep(0.01)

        async def tts_wrapper():
            while not self._cancel_event.is_set():
                try:
                    chunk = await asyncio.wait_for(tts_queue.get(), timeout=0.1)
                    yield chunk
                except asyncio.TimeoutError:
                    if self._cancel_event.is_set():
                        break

        async with asyncio.TaskGroup() as tg:
            tg.create_task(stt_wrapper())
            tg.create_task(llm_wrapper())
            async for chunk in tts_wrapper():
                yield chunk

    async def _process_stt(self, audio_chunk: bytes):
        from app.services.paraformer_stt_service import paraformer_stt_service
        async for evt, text in paraformer_stt_service.transcribe_stream_events(audio_chunk):
            if self._cancel_event and self._cancel_event.is_set():
                break
            self._llm_queue.append(text)

    async def _process_llm(self, messages: list) -> AsyncIterator[bytes]:
        from app.agents.interviewer_agent import InterviewerAgent
        agent = InterviewerAgent()
        async for chunk in agent.chat(messages, stream=True):
            if self._cancel_event.is_set():
                break
            yield chunk

    async def _process_tts(self):
        from app.services.qwen_tts_service import qwen_tts_service
        async for chunk in qwen_tts_service.stream_synthesize(""):
            if self._cancel_event.is_set():
                break
            yield chunk

    def cancel(self) -> None:
        """Cancel all ongoing processing."""
        if self._cancel_event is not None:
            self._cancel_event.set()


streaming_coordinator = StreamingCoordinator()
from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.services.rag_service import rag_service
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service
from app.services.tts_text_service import tts_text_normalizer


async def run_startup_tasks() -> None:
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.TTS_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    tts_text_normalizer.force_reload()
    await stt_service.ensure_model_ready()
    await tts_service.ensure_ready()
    await rag_service.ensure_indexes()

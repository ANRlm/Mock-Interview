from __future__ import annotations

from fastapi import APIRouter

from app.services.tts_metrics_service import tts_metrics_service

router = APIRouter(prefix="/tts", tags=["tts"])


@router.get("/metrics")
async def get_tts_metrics() -> dict:
    return tts_metrics_service.summary()


@router.delete("/metrics")
async def reset_tts_metrics() -> dict:
    tts_metrics_service.clear()
    return {"ok": True}

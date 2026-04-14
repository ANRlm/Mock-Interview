from fastapi import APIRouter

from . import interview_ws, stt_ws, tts_ws

router = APIRouter()

router.include_router(interview_ws.router, tags=["websocket"])
router.include_router(stt_ws.router, tags=["websocket"])
router.include_router(tts_ws.router, tags=["websocket"])

from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database import AsyncSessionLocal, get_db
from app.models.behavior_log import BehaviorLog
from app.models.session import InterviewSession
from app.models.user import User  # noqa: F401
from app.schemas import BehaviorBatchInput
from app.services.vision_service import vision_service

router = APIRouter(prefix="/sessions", tags=["behavior"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/{session_id}/behavior", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("120/minute")
async def post_behavior(
    request: Request,
    session_id: UUID,
    payload: BehaviorBatchInput,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, str]:
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    frames = payload.frames

    async def _persist() -> None:
        async with AsyncSessionLocal() as async_db:
            for frame in frames:
                emotion, confidence = await vision_service.analyze_frame(
                    frame.image_base64
                )
                item = BehaviorLog(
                    session_id=session_id,
                    frame_second=frame.frame_second,
                    emotion=emotion,
                    emotion_confidence=confidence,
                    eye_contact_score=frame.eye_contact_score,
                    head_pose_score=frame.head_pose_score,
                    gaze_x=frame.gaze_x,
                    gaze_y=frame.gaze_y,
                )
                async_db.add(item)
            await async_db.commit()

    asyncio.create_task(_persist())
    return {"status": "queued"}

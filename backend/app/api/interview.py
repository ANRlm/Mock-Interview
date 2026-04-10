from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import ConversationMessage
from app.models.session import InterviewSession, SessionStatus
from app.schemas import MessageRead, SessionCreate, SessionRead, SessionUpdate

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate, db: AsyncSession = Depends(get_db)
) -> SessionRead:
    session = InterviewSession(
        job_role=payload.job_role,
        sub_role=payload.sub_role,
        status=SessionStatus.setup,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionRead.model_validate(session, from_attributes=True)


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> SessionRead:
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionRead.model_validate(session, from_attributes=True)


@router.patch("/{session_id}", response_model=SessionRead)
async def update_session(
    session_id: UUID,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> SessionRead:
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.now(timezone.utc)
    session.status = payload.status
    if payload.status == SessionStatus.active and session.started_at is None:
        session.started_at = now
    if payload.status == SessionStatus.completed:
        session.ended_at = now

    await db.commit()
    await db.refresh(session)
    return SessionRead.model_validate(session, from_attributes=True)


@router.get("/{session_id}/messages", response_model=list[MessageRead])
async def get_messages(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[MessageRead]:
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(
            ConversationMessage.turn_index.asc(), ConversationMessage.timestamp.asc()
        )
    )
    messages = result.scalars().all()
    return [
        MessageRead.model_validate(message, from_attributes=True)
        for message in messages
    ]

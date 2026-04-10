from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BehaviorLog(Base):
    __tablename__ = "behavior_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    frame_second: Mapped[int] = mapped_column(Integer, nullable=False)
    emotion: Mapped[str] = mapped_column(String(32), nullable=False, default="neutral")
    emotion_confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    eye_contact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    head_pose_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gaze_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    gaze_y: Mapped[float | None] = mapped_column(Float, nullable=True)

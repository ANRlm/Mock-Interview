from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SessionStatus(str, enum.Enum):
    setup = "setup"
    active = "active"
    completed = "completed"


class JobRole(str, enum.Enum):
    programmer = "programmer"
    lawyer = "lawyer"
    doctor = "doctor"
    teacher = "teacher"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_role: Mapped[JobRole] = mapped_column(Enum(JobRole), nullable=False)
    sub_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resume_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_parsed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus),
        nullable=False,
        default=SessionStatus.setup,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

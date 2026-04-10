from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    llm_overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    llm_professional_score: Mapped[float] = mapped_column(Float, nullable=False)
    llm_communication_score: Mapped[float] = mapped_column(Float, nullable=False)
    llm_logic_score: Mapped[float] = mapped_column(Float, nullable=False)
    llm_evaluation_text: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    improvements: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    fluency_score: Mapped[float] = mapped_column(Float, nullable=False)
    speech_rate_wpm: Mapped[float] = mapped_column(Float, nullable=False)
    filler_word_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    pause_frequency: Mapped[float] = mapped_column(Float, nullable=False)
    fluency_detail: Mapped[dict] = mapped_column(JSON, nullable=False)

    behavior_score: Mapped[float] = mapped_column(Float, nullable=False)
    avg_eye_contact: Mapped[float] = mapped_column(Float, nullable=False)
    dominant_emotion: Mapped[str] = mapped_column(String(32), nullable=False)
    behavior_detail: Mapped[dict] = mapped_column(JSON, nullable=False)

    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

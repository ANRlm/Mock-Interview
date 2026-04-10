from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LLMRuntimeConfig(Base):
    __tablename__ = "llm_runtime_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    active_profile: Mapped[str] = mapped_column(
        String(24), nullable=False, default="local"
    )
    active_model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    disable_thinking_override: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

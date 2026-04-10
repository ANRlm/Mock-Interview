from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.llm_profile_service import llm_profile_service

router = APIRouter(prefix="/llm", tags=["llm-config"])


class LLMRuntimeUpdate(BaseModel):
    profile: str = Field(pattern="^(local|cloud)$")
    model: str | None = Field(default=None, max_length=160)
    disable_thinking: bool | None = None


@router.get("/profiles")
async def get_profiles(db: AsyncSession = Depends(get_db)) -> dict:
    return await llm_profile_service.list_profiles(db)


@router.put("/runtime")
async def update_runtime(
    payload: LLMRuntimeUpdate, db: AsyncSession = Depends(get_db)
) -> dict:
    try:
        return await llm_profile_service.update_runtime_profile(
            db,
            profile_name=payload.profile,
            model=payload.model,
            disable_thinking=payload.disable_thinking,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

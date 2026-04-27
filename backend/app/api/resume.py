from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.resume_agent import ResumeAgent
from app.api.dependencies import get_current_user
from app.api.interview import _assert_session_owner
from app.config import settings
from app.database import get_db
from app.models.session import InterviewSession
from app.models.user import User  # noqa: F401
from app.services.resume_service import (
    parse_resume,
    parse_resume_text,
    read_resume_text,
)

router = APIRouter(prefix="/sessions", tags=["resume"])

_DEFAULT_SUMMARY = "简历已上传，暂未解析。"


@router.post("/{session_id}/resume", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    session_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    session = await db.get(InterviewSession, session_id)
    _assert_session_owner(session, current_user)

    suffix = Path(file.filename or "resume.pdf").suffix.lower()
    if suffix not in {".pdf", ".txt", ".md", ".docx", ".doc"}:
        raise HTTPException(status_code=400, detail="Unsupported resume file type")

    target_dir = Path(settings.UPLOAD_DIR) / str(session_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"resume{suffix}"

    content = await file.read()
    target_path.write_bytes(content)

    session.resume_path = str(target_path)
    resume_text = read_resume_text(str(target_path))

    if resume_text.strip():
        parsed = parse_resume_text(resume_text)
        llm_structured = await ResumeAgent().structure_resume(resume_text)
        parsed = _merge_parsed_resume(parsed, llm_structured)
    else:
        parsed = parse_resume(str(target_path))

    session.resume_parsed = {
        **parsed,
        "filename": file.filename,
        "bytes": len(content),
    }
    await db.commit()

    return {"status": "uploaded", "path": str(target_path)}


@router.get("/{session_id}/resume")
async def get_resume(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = await db.get(InterviewSession, session_id)
    _assert_session_owner(session, current_user)
    return session.resume_parsed or {"status": "empty"}


def _merge_parsed_resume(
    parsed: dict[str, Any],
    structured: dict[str, Any],
) -> dict[str, Any]:
    parsed_summary = str(parsed.get("summary") or "").strip()
    structured_summary = str(structured.get("summary") or "").strip()

    summary = parsed_summary or _DEFAULT_SUMMARY
    if structured_summary and structured_summary != _DEFAULT_SUMMARY:
        summary = structured_summary

    return {
        "name": _pick_text(structured.get("name"), parsed.get("name")),
        "gender": _pick_text(structured.get("gender"), parsed.get("gender")),
        "major": _pick_text(structured.get("major"), parsed.get("major")),
        "education_level": _pick_text(
            structured.get("education_level"),
            parsed.get("education_level"),
        ),
        "self_introduction": _pick_text(
            structured.get("self_introduction"),
            parsed.get("self_introduction") or summary,
        ),
        "summary": summary,
        "raw_summary": parsed_summary,
        "education": _pick_list(structured.get("education"), parsed.get("education")),
        "experience": _pick_list(
            structured.get("experience"),
            parsed.get("experience"),
        ),
        "projects": _pick_list(structured.get("projects"), parsed.get("projects")),
        "awards": _pick_list(structured.get("awards"), parsed.get("awards")),
        "target_position": _pick_text(
            structured.get("target_position"),
            parsed.get("target_position"),
        ),
        "skills": _pick_list(structured.get("skills"), parsed.get("skills")),
    }


def _pick_list(primary: Any, fallback: Any) -> list[str]:
    primary_list = _normalize_list(primary)
    if primary_list:
        return primary_list
    return _normalize_list(fallback)


def _pick_text(primary: Any, fallback: Any) -> str:
    primary_text = str(primary or "").strip()
    if primary_text:
        return primary_text
    return str(fallback or "").strip()


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []

    items: list[Any]
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [value]
    else:
        return []

    output: list[str] = []
    for item in items:
        text = str(item).strip()
        if text and text not in output:
            output.append(text)
    return output[:8]

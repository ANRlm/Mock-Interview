from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.report import InterviewReport
from app.models.session import InterviewSession
from app.schemas import ReportGenerateResponse, ReportRead
from app.services.report_service import is_report_pending, trigger_report_generation

router = APIRouter(prefix="/sessions", tags=["report"])


@router.post(
    "/{session_id}/report",
    response_model=ReportGenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_report(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> ReportGenerateResponse:
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    pending_status = await trigger_report_generation(session_id)
    return ReportGenerateResponse(status=pending_status, session_id=session_id)


@router.get("/{session_id}/report", response_model=ReportRead)
async def get_report(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> ReportRead | JSONResponse:
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    report = await db.scalar(
        select(InterviewReport).where(InterviewReport.session_id == session_id)
    )
    if report is None:
        if is_report_pending(session_id):
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"detail": "Report generating"},
            )
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportRead.model_validate(report, from_attributes=True)

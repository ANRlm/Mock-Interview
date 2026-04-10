from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.message import MessageRole
from app.models.session import JobRole, SessionStatus


class SessionCreate(BaseModel):
    job_role: JobRole
    sub_role: str | None = None


class SessionUpdate(BaseModel):
    status: SessionStatus


class SessionRead(BaseModel):
    id: UUID
    job_role: JobRole
    sub_role: str | None
    status: SessionStatus
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageRead(BaseModel):
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    timestamp: datetime
    turn_index: int

    model_config = {"from_attributes": True}


class InterviewInput(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class WsServerMessage(BaseModel):
    type: str
    data: dict | None = None


class ReportGenerateResponse(BaseModel):
    status: str
    session_id: UUID


class DimensionScore(BaseModel):
    score: float
    comment: str


class ReportPayload(BaseModel):
    overall_score: float
    dimensions: dict[str, DimensionScore]
    strengths: list[str]
    improvements: list[str]
    overall_evaluation: str


class ReportRead(BaseModel):
    session_id: UUID
    llm_overall_score: float
    llm_professional_score: float
    llm_communication_score: float
    llm_logic_score: float
    llm_evaluation_text: str
    fluency_score: float
    behavior_score: float
    total_score: float
    strengths: list[str]
    improvements: list[str]
    generated_at: datetime

    model_config = {"from_attributes": True}


class BehaviorFrameInput(BaseModel):
    frame_second: int = Field(ge=0)
    eye_contact_score: float = Field(ge=0.0, le=1.0)
    head_pose_score: float = Field(ge=0.0, le=1.0)
    gaze_x: float | None = None
    gaze_y: float | None = None
    image_base64: str | None = None


class BehaviorBatchInput(BaseModel):
    frames: list[BehaviorFrameInput]

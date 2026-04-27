from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.agents.scorer_agent import ScorerAgent
from app.database import AsyncSessionLocal
from app.models.behavior_log import BehaviorLog
from app.models.message import ConversationMessage
from app.models.report import InterviewReport
from app.models.session import InterviewSession
from app.services.fluency_service import analyze_fluency
from app.services.vision_service import vision_service

logger = logging.getLogger(__name__)


async def trigger_report_generation(session_id: UUID) -> str:
    async with AsyncSessionLocal() as db:
        session = await db.get(InterviewSession, session_id)
        if session is None:
            return "error: session not found"
        if session.report_generating:
            return "pending"
        session.report_generating = True
        await db.commit()
    asyncio.create_task(_generate_report(session_id))
    return "pending"


def _apply_report_fields(
    report: "InterviewReport",
    *,
    llm_json: dict,
    dims: dict,
    overall: float,
    professional: float,
    communication: float,
    logic: float,
    fluency: dict,
    behavior_score: float,
    avg_eye_contact: float,
    dominant_emotion: str,
    behavior_detail: dict,
    total_score: float,
) -> None:
    """Apply all computed fields to a report object (create or update path)."""
    report.llm_overall_score = overall
    report.llm_professional_score = professional
    report.llm_communication_score = communication
    report.llm_logic_score = logic
    report.llm_evaluation_text = str(llm_json.get("overall_evaluation", "综合表现良好。"))
    report.strengths = [str(item) for item in llm_json.get("strengths", [])]
    report.improvements = [str(item) for item in llm_json.get("improvements", [])]
    report.fluency_score = float(fluency["fluency_score"])
    report.speech_rate_wpm = float(fluency["speech_rate_wpm"])
    report.filler_word_ratio = float(fluency["filler_word_ratio"])
    report.pause_frequency = float(fluency["pause_frequency"])
    report.fluency_detail = fluency["detail"]
    report.behavior_score = behavior_score
    report.avg_eye_contact = avg_eye_contact
    report.dominant_emotion = dominant_emotion
    report.behavior_detail = behavior_detail
    report.total_score = total_score
    report.generated_at = datetime.now(timezone.utc)


async def _generate_report(session_id: UUID) -> None:
    try:
        async with AsyncSessionLocal() as db:
            session = await db.get(InterviewSession, session_id)
            if session is None:
                logger.warning("Report generation: session %s not found", session_id)
                return

            messages_result = await db.execute(
                select(ConversationMessage)
                .where(ConversationMessage.session_id == session_id)
                .order_by(
                    ConversationMessage.turn_index.asc(),
                    ConversationMessage.timestamp.asc(),
                )
            )
            messages = messages_result.scalars().all()
            transcript = "\n".join(
                f"[{msg.role.value}] {msg.content.strip()}"
                for msg in messages
                if msg.content.strip()
            )

            scorer = ScorerAgent()
            llm_json = await scorer.score_interview(
                job_role=session.job_role.value,
                resume_summary=(session.resume_parsed or {}).get("summary", "暂无简历"),
                messages_text=transcript,
            )

            dims = llm_json.get("dimensions", {})
            professional = float(
                (dims.get("professional_knowledge") or {}).get("score", 75)
            )
            communication = float((dims.get("communication") or {}).get("score", 75))
            logic = float((dims.get("logical_thinking") or {}).get("score", 75))
            overall = float(
                llm_json.get(
                    "overall_score", (professional + communication + logic) / 3
                )
            )

            fluency = analyze_fluency(transcript)

            behavior_result = await db.execute(
                select(BehaviorLog)
                .where(BehaviorLog.session_id == session_id)
                .order_by(BehaviorLog.timestamp.asc())
            )
            behavior_logs = behavior_result.scalars().all()
            emotions = [item.emotion for item in behavior_logs]
            emotion_confidences = [item.emotion_confidence for item in behavior_logs]
            eye_scores = [item.eye_contact_score for item in behavior_logs]
            head_pose_scores = [item.head_pose_score for item in behavior_logs]
            gaze_x_values = [
                item.gaze_x for item in behavior_logs if item.gaze_x is not None
            ]
            gaze_y_values = [
                item.gaze_y for item in behavior_logs if item.gaze_y is not None
            ]

            behavior_summary = vision_service.summarize(
                emotions=emotions,
                emotion_confidences=emotion_confidences,
                eye_scores=eye_scores,
                head_pose_scores=head_pose_scores,
                gaze_x_values=gaze_x_values,
                gaze_y_values=gaze_y_values,
            )

            dominant_emotion = behavior_summary.dominant_emotion
            avg_eye_contact = behavior_summary.avg_eye_contact
            behavior_score = behavior_summary.behavior_score

            total_score = round(
                (
                    overall * 0.6
                    + float(fluency["fluency_score"]) * 0.2
                    + behavior_score * 0.2
                ),
                2,
            )

            behavior_detail_dict = {
                "sample_count": len(behavior_logs),
                "emotion_distribution": _emotion_distribution(emotions),
                "attention_score": behavior_summary.attention_score,
                "posture_score": behavior_summary.posture_score,
                "engagement_score": behavior_summary.engagement_score,
                "gaze_stability": behavior_summary.gaze_stability,
                "emotion_confidence": behavior_summary.emotion_confidence,
                "recommendations": behavior_summary.recommendations,
            }

            report = await db.scalar(
                select(InterviewReport).where(InterviewReport.session_id == session_id)
            )
            if report is None:
                report = InterviewReport(session_id=session_id)
                db.add(report)

            _apply_report_fields(
                report,
                llm_json=llm_json,
                dims=dims,
                overall=overall,
                professional=professional,
                communication=communication,
                logic=logic,
                fluency=fluency,
                behavior_score=behavior_score,
                avg_eye_contact=avg_eye_contact,
                dominant_emotion=dominant_emotion,
                behavior_detail=behavior_detail_dict,
                total_score=total_score,
            )

            await db.commit()
    except Exception as exc:
        logger.exception("Report generation failed for session %s: %s", session_id, exc)
    finally:
        async with AsyncSessionLocal() as db:
            session = await db.get(InterviewSession, session_id)
            if session is not None:
                session.report_generating = False
                await db.commit()


async def is_report_pending(session_id: UUID) -> bool:
    async with AsyncSessionLocal() as db:
        session = await db.get(InterviewSession, session_id)
        if session is None:
            return False
        return session.report_generating


def _emotion_distribution(emotions: list[str]) -> dict[str, int]:
    output: dict[str, int] = {}
    for emotion in emotions:
        output[emotion] = output.get(emotion, 0) + 1
    return output

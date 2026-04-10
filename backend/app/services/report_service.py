from __future__ import annotations

import asyncio
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

_report_tasks: set[UUID] = set()


async def trigger_report_generation(session_id: UUID) -> str:
    if session_id in _report_tasks:
        return "pending"

    _report_tasks.add(session_id)
    asyncio.create_task(_generate_report(session_id))
    return "pending"


async def _generate_report(session_id: UUID) -> None:
    try:
        async with AsyncSessionLocal() as db:
            session = await db.get(InterviewSession, session_id)
            if session is None:
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

            report = await db.scalar(
                select(InterviewReport).where(InterviewReport.session_id == session_id)
            )
            if report is None:
                report = InterviewReport(
                    session_id=session_id,
                    llm_overall_score=overall,
                    llm_professional_score=professional,
                    llm_communication_score=communication,
                    llm_logic_score=logic,
                    llm_evaluation_text=str(
                        llm_json.get("overall_evaluation", "综合表现良好。")
                    ),
                    strengths=[str(item) for item in llm_json.get("strengths", [])],
                    improvements=[
                        str(item) for item in llm_json.get("improvements", [])
                    ],
                    fluency_score=float(fluency["fluency_score"]),
                    speech_rate_wpm=float(fluency["speech_rate_wpm"]),
                    filler_word_ratio=float(fluency["filler_word_ratio"]),
                    pause_frequency=float(fluency["pause_frequency"]),
                    fluency_detail=fluency["detail"],
                    behavior_score=behavior_score,
                    avg_eye_contact=avg_eye_contact,
                    dominant_emotion=dominant_emotion,
                    behavior_detail={
                        "sample_count": len(behavior_logs),
                        "emotion_distribution": _emotion_distribution(emotions),
                        "attention_score": behavior_summary.attention_score,
                        "posture_score": behavior_summary.posture_score,
                        "engagement_score": behavior_summary.engagement_score,
                        "gaze_stability": behavior_summary.gaze_stability,
                        "emotion_confidence": behavior_summary.emotion_confidence,
                        "recommendations": behavior_summary.recommendations,
                    },
                    total_score=total_score,
                    generated_at=datetime.now(timezone.utc),
                )
                db.add(report)
            else:
                report.llm_overall_score = overall
                report.llm_professional_score = professional
                report.llm_communication_score = communication
                report.llm_logic_score = logic
                report.llm_evaluation_text = str(
                    llm_json.get("overall_evaluation", "综合表现良好。")
                )
                report.strengths = [str(item) for item in llm_json.get("strengths", [])]
                report.improvements = [
                    str(item) for item in llm_json.get("improvements", [])
                ]
                report.fluency_score = float(fluency["fluency_score"])
                report.speech_rate_wpm = float(fluency["speech_rate_wpm"])
                report.filler_word_ratio = float(fluency["filler_word_ratio"])
                report.pause_frequency = float(fluency["pause_frequency"])
                report.fluency_detail = fluency["detail"]
                report.behavior_score = behavior_score
                report.avg_eye_contact = avg_eye_contact
                report.dominant_emotion = dominant_emotion
                report.behavior_detail = {
                    "sample_count": len(behavior_logs),
                    "emotion_distribution": _emotion_distribution(emotions),
                    "attention_score": behavior_summary.attention_score,
                    "posture_score": behavior_summary.posture_score,
                    "engagement_score": behavior_summary.engagement_score,
                    "gaze_stability": behavior_summary.gaze_stability,
                    "emotion_confidence": behavior_summary.emotion_confidence,
                    "recommendations": behavior_summary.recommendations,
                }
                report.total_score = total_score
                report.generated_at = datetime.now(timezone.utc)

            await db.commit()
    finally:
        _report_tasks.discard(session_id)


def is_report_pending(session_id: UUID) -> bool:
    return session_id in _report_tasks


def _emotion_distribution(emotions: list[str]) -> dict[str, int]:
    output: dict[str, int] = {}
    for emotion in emotions:
        output[emotion] = output.get(emotion, 0) + 1
    return output

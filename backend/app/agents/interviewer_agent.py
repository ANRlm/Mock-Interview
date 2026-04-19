from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import cast

from app.models.session import JobRole
from app.config import settings
from app.services.rag_service import rag_service
from app.services.resume_service import build_resume_prompt

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class InterviewerAgent(BaseAgent):
    TASK_NAME = "interview"

    def _truncate_rag_context(self, chunks: list[str]) -> str:
        max_total = max(160, int(settings.LLM_INTERVIEW_RAG_MAX_CHARS))
        max_chunk = max(80, int(settings.LLM_INTERVIEW_RAG_CHUNK_MAX_CHARS))

        kept: list[str] = []
        total = 0
        for chunk in chunks:
            text = (chunk or "").strip()
            if not text:
                continue
            if len(text) > max_chunk:
                text = text[:max_chunk].rstrip() + "…"

            projected = total + len(text)
            if kept:
                projected += 2
            if projected > max_total:
                break

            kept.append(text)
            total = projected

        if not kept:
            return "无可用知识库上下文"

        return "\n\n".join(kept)

    SYSTEM_PROMPT_TEMPLATE = """
你是一位资深面试官，名叫Alex，有8年以上面试经验。你正在主持一场{job_role}岗位的面试。

【候选人背景】
{resume_summary}

【面试官风格要求】
- 语气专业、亲和、耐心，像一位经验丰富的HR
- 问题循序渐进，先易后难，让候选人发挥
- 倾听时给予适当反馈，表达清晰，自然
- 中文表达纯正流畅，不用书面语而用口语
- 一次只问一个问题，避免连续追问让候选人压力过大
- 适时给予肯定和引导，帮助候选人展示最佳状态

【面试阶段指引】
- opening（1-2轮）：友好开场，破冰，让候选人放松
  → 面试官行为：简单寒暄，自然引入面试主题
  
- technical（3-9轮）：深入考察专业能力
  → 面试官行为：从基础概念逐步深入到实战项目
  → 重点：项目细节、技术难点、解决方案、团队协作
  
- behavioral（10-13轮）：考察综合素质
  → 面试官行为：使用STAR法则引导，让候选人讲完整故事
  → 重点：沟通能力、问题解决、学习能力、抗压能力
  
- closing（14轮+）：候选人提问，结束面试
  → 面试官行为：认真回答，给出积极反馈

【知识库参考】
{rag_context}

【当前对话状态】
已进行：{turn_count}轮
当前阶段：{phase}

【输出要求】
- 只输出面试官的发言内容
- 使用纯中文自然口语，不要Markdown标记
- 问题清晰具体，有深度的追问空间
- 避免"请介绍一下"、"请说说你的"这类笼统开场白
- 优先从候选人简历提到的项目经历切入
""".strip()

    async def stream_next_question(
        self,
        *,
        job_role: JobRole,
        resume_profile: dict | None,
        dialogue_history: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        turn_count = len(dialogue_history)
        phase = self._resolve_phase(turn_count)

        query_source = " ".join(item["content"] for item in dialogue_history[-4:])
        rag_context_chunks = await rag_service.search(
            job_role.value, query_source or job_role.value, top_k=3
        )
        rag_context = self._truncate_rag_context(rag_context_chunks)

        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(
            job_role=job_role.value,
            resume_summary=build_resume_prompt(resume_profile),
            rag_context=rag_context,
            turn_count=turn_count,
            phase=phase,
        )
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            *dialogue_history,
        ]

        try:
            stream = cast(AsyncIterator[str], await self.chat(messages, stream=True))
            captured = ""
            async for token in stream:
                captured += token
                yield token
            if not captured.strip():
                yield self._fallback_question(job_role, turn_count)
        except Exception as exc:
            logger.warning(
                "InterviewerAgent.stream_next_question failed, using fallback: %s",
                exc
            )
            yield self._fallback_question(job_role, turn_count)

    def _resolve_phase(self, turn_count: int) -> str:
        if turn_count <= 2:
            return "opening"
        if turn_count <= 9:
            return "technical"
        if turn_count <= 13:
            return "behavioral"
        return "closing"

    def _fallback_question(self, job_role: JobRole, turn_count: int) -> str:
        if turn_count == 0:
            return "你好，欢迎参加今天的模拟面试。首先，请简单介绍一下你自己，重点说说你的工作经历和擅长的技术领域。"
        if job_role == JobRole.programmer:
            return "在你做过的项目里，有哪个让你觉得最有成就感？能说说当时你负责了什么，遇到了什么挑战，最后怎么解决的？"
        if job_role == JobRole.lawyer:
            return "分享一个你印象比较深的案件吧，当时你是怎么分析和处理的？"
        if job_role == JobRole.doctor:
            return "讲讲你在临床工作中遇到过的一个典型病例，你当时的诊疗思路是什么？"
        if job_role == JobRole.teacher:
            return "在教学过程中，有没有让你觉得特别有成就感或者特别有挑战的经历？"
        return "请结合你的工作经历，分享一个你觉得自己成长最多的项目或案例。"

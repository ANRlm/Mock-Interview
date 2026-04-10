from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

from app.models.session import JobRole
from app.services.rag_service import rag_service
from app.services.resume_service import build_resume_prompt

from .base_agent import BaseAgent


class InterviewerAgent(BaseAgent):
    SYSTEM_PROMPT_TEMPLATE = """
你是一位经验丰富的{job_role}领域面试官，名叫"Alex"。
当前候选人信息：{resume_summary}
面试重点方向：{rag_context}
已进行对话轮数：{turn_count}
面试阶段：{phase}

要求：
- 每次只问一个问题，问题清晰简洁
- 根据候选人上一轮回答进行追问或转换话题
- opening 阶段：自我介绍，破冰
- technical 阶段：专业知识、项目经历深挖
- behavioral 阶段：情境题（STAR 法则引导）
- closing 阶段：候选人提问环节，结束面试
- 如候选人简历中提到具体项目，优先追问项目细节
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
        rag_context = (
            "\n\n".join(rag_context_chunks)
            if rag_context_chunks
            else "无可用知识库上下文"
        )

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
        except Exception:
            yield self._fallback_question(job_role, turn_count)

    def _resolve_phase(self, turn_count: int) -> str:
        if turn_count <= 2:
            return "opening"
        if turn_count <= 8:
            return "technical"
        if turn_count <= 12:
            return "behavioral"
        return "closing"

    def _fallback_question(self, job_role: JobRole, turn_count: int) -> str:
        if turn_count == 0:
            return "欢迎参加模拟面试。请先做一个 1 分钟左右的自我介绍。"
        if job_role == JobRole.programmer:
            return "请介绍一个你最有代表性的项目，并说明你负责的核心模块与技术取舍。"
        if job_role == JobRole.lawyer:
            return "请分享一个你处理过的复杂案件，重点说明你的法律分析路径。"
        if job_role == JobRole.doctor:
            return "请讲述一次你参与的典型病例诊疗过程，以及你的决策依据。"
        return "请分享一次你在教学中遇到的困难场景，以及你如何解决。"

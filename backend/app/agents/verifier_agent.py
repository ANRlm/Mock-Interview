from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent


class VerifierAgent(BaseAgent):
    TASK_NAME = "verifier"

    SYSTEM_PROMPT = """
你是面试问题质量审核助手。你的任务是检查面试官问题是否清晰、单一、可回答。
请返回 JSON：
{
  "approved": true/false,
  "reason": "简要原因",
  "rewritten_question": "若不通过则给出改写后的单一问题；通过可为空"
}
仅输出 JSON。
""".strip()

    async def verify_question(self, question: str) -> dict[str, Any]:
        prompt = (
            "请审核下面的问题是否满足单轮面试提问规范：\n"
            "- 只问一个问题\n"
            "- 语义清晰\n"
            "- 避免过长复合句\n"
            "- 避免一次追问多个维度\n\n"
            f"问题文本:\n{question.strip()}"
        )
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            result = await self.chat_json(messages)
        except Exception:
            return {
                "approved": True,
                "reason": "verifier_fallback",
                "rewritten_question": "",
            }

        approved = bool(result.get("approved", True))
        reason = str(result.get("reason") or "").strip()
        rewritten = str(result.get("rewritten_question") or "").strip()
        return {
            "approved": approved,
            "reason": reason,
            "rewritten_question": rewritten,
        }

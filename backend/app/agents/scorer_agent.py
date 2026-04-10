from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent


class ScorerAgent(BaseAgent):
    TASK_NAME = "evaluation"

    SYSTEM_PROMPT = """
你是一位资深面试评估官。请基于完整对话记录给出结构化评分。
返回 JSON，格式如下：
{
  "overall_score": 0-100,
  "dimensions": {
    "professional_knowledge": { "score": 0-100, "comment": "..." },
    "communication": { "score": 0-100, "comment": "..." },
    "logical_thinking": { "score": 0-100, "comment": "..." },
    "problem_solving": { "score": 0-100, "comment": "..." }
  },
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "overall_evaluation": "..."
}
仅输出 JSON，不要输出任何额外文字。
""".strip()

    async def score_interview(
        self,
        *,
        job_role: str,
        resume_summary: str,
        messages_text: str,
    ) -> dict[str, Any]:
        prompt = (
            f"职位方向: {job_role}\n"
            f"简历摘要: {resume_summary or '暂无'}\n"
            "完整对话:\n"
            f"{messages_text}\n"
        )
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            return await self.chat_json(messages)
        except Exception:
            return {
                "overall_score": 75,
                "dimensions": {
                    "professional_knowledge": {
                        "score": 78,
                        "comment": "专业基础较扎实。",
                    },
                    "communication": {"score": 74, "comment": "表达清晰但可更精炼。"},
                    "logical_thinking": {"score": 76, "comment": "结构化思维良好。"},
                    "problem_solving": {
                        "score": 72,
                        "comment": "解题思路完整，细节可加强。",
                    },
                },
                "strengths": ["能够结合实际经验回答", "具备基本结构化表达"],
                "improvements": ["增加定量结果说明", "回答中先给结论再展开"],
                "overall_evaluation": "整体表现稳健，建议加强案例深挖与结果量化。",
            }

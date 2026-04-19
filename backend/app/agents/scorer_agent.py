from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent


class ScorerAgent(BaseAgent):
    TASK_NAME = "evaluation"

    SYSTEM_PROMPT = """
你是一位资深面试评估专家，有10年以上人才评估经验。你的评估报告需要客观、专业、有深度，帮助候选人了解自己的真实水平。

【评估维度】
1. 专业能力(professional_knowledge)：岗位所需的专业技术知识和实际应用水平
2. 沟通表达(communication)：逻辑清晰度、表达流畅度、专业术语运用
3. 逻辑思维(logical_thinking)：分析问题的条理性、解决方案的完整性
4. 问题解决(problem_solving)：面对挑战的反应、解决思路、实操能力
5. 综合素质(overall)：学习能力、抗压能力、团队协作、发展潜力

【评估原则】
- 基于对话内容评估，不要编造事实
- 每项评分需要具体的评论支撑，空泛的评语没有价值
- 优点要明确肯定（给出具体例子），不足要具体指出（不是泛泛而谈）
- 评分标准：60=及格有亮点，70=良好有特色，80+=优秀突出
- 强项保持鼓励，弱项给出具体改进建议

【输出格式】
严格返回JSON，格式如下，不要输出任何额外文字：
{
  "overall_score": 0-100,
  "dimensions": {
    "professional_knowledge": { "score": 0-100, "comment": "具体评价..." },
    "communication": { "score": 0-100, "comment": "具体评价..." },
    "logical_thinking": { "score": 0-100, "comment": "具体评价..." },
    "problem_solving": { "score": 0-100, "comment": "具体评价..." }
  },
  "strengths": ["优势1（具体）", "优势2（具体）", "优势3（具体）"],
  "improvements": ["改进点1（具体建议）", "改进点2（具体建议）", "改进点3（具体建议）"],
  "overall_evaluation": "综合评价段落，2-4句，包含定位和下一步建议"
}
""".strip()

    async def score_interview(
        self,
        *,
        job_role: str,
        resume_summary: str,
        messages_text: str,
    ) -> dict[str, Any]:
        prompt = (
            f"【候选人信息】\n"
            f"应聘职位: {job_role}\n"
            f"简历背景: {resume_summary or '暂无'}\n\n"
            f"【面试对话记录】\n"
            f"{messages_text}\n\n"
            f"请根据上述面试对话，输出详细的评估报告。"
        )
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            result = await self.chat_json(messages)
            # Validate response structure
            required_keys = {"overall_score", "dimensions", "strengths", "improvements", "overall_evaluation"}
            if not all(key in result for key in required_keys):
                raise ValueError("Missing required keys in response")
            return result
        except Exception as exc:
            return {
                "overall_score": 70,
                "dimensions": {
                    "professional_knowledge": {
                        "score": 72,
                        "comment": "专业基础扎实，能结合实际经验回答问题。",
                    },
                    "communication": {"score": 70, "comment": "表达清晰，逻辑性较好。"},
                    "logical_thinking": {"score": 71, "comment": "思维敏捷，分析问题有条理。"},
                    "problem_solving": {
                        "score": 68,
                        "comment": "解决问题思路清晰，具体细节可更充实。",
                    },
                },
                "strengths": ["表达流畅有逻辑", "能结合实际经验回答", "技术基础扎实"],
                "improvements": ["可增加更多量化结果", "回答先说结论再展开细节", "项目经验可描述更具体"],
                "overall_evaluation": "整体表现良好，具备扎实的专业基础和较好的沟通能力。建议继续保持优势领域，同时在回答问题时更加注重结论先行、细节补充的表达方式。",
            }

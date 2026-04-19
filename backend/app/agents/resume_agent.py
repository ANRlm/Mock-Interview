from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent


_DEFAULT_PARSED_RESUME: dict[str, Any] = {
    "name": "",
    "gender": "",
    "major": "",
    "education_level": "",
    "self_introduction": "",
    "summary": "简历已上传，暂未解析。",
    "education": [],
    "experience": [],
    "projects": [],
    "awards": [],
    "target_position": "",
    "skills": [],
}


class ResumeAgent(BaseAgent):
    TASK_NAME = "resume"

    SYSTEM_PROMPT = """
你是一位资深HR，擅长从简历文本中提取关键信息。你的提取必须准确、完整、结构化。

【提取要求】
- 严格按照提供的字段提取，不要添加不在列表中的字段
- 如果某字段在简历中找不到对应信息，返回空字符串或空数组
- name: 姓名，只提取中文名或英文名，不要包含头衔
- gender: 性别，提取"男"或"女"
- major: 专业名称，提取标准专业名
- education_level: 学历层次，提取"博士"、"硕士"、"本科"、"大专"、"中专"等
- self_introduction: 自我介绍，2-4句概括个人特点和优势
- summary: 综合概述，2-4句描述整体背景和亮点
- education: 教育经历数组，每项包含学校、学位、时间
- experience: 工作/实习经历数组，每项包含公司、职位、时间、职责
- projects: 项目经历数组，每项包含项目名、角色、核心贡献、技术栈
- awards: 获奖/证书数组，每项包含奖项名称、时间、级别
- target_position: 目标职位/求职意向
- skills: 技能清单数组，提取核心技术技能（6-10项）

【重要原则】
- 只提取简历中明确存在的信息，不要推测或编造
- 如果信息模糊，标注为"未明确"
- 时间格式统一为"YYYY-MM"或"YYYY年"格式
- 技能要具体（React而非前端框架）
""".strip()

    async def structure_resume(self, resume_text: str) -> dict[str, Any]:
        prompt = (
            "请从以下简历文本中提取结构化信息，并严格返回JSON格式。\n\n"
            "【字段要求】\n"
            "- name: string，姓名\n"
            "- gender: string，性别（男/女）\n"
            "- major: string，专业名称\n"
            "- education_level: string，学历（博士/硕士/本科/大专/中专）\n"
            "- self_introduction: string，2-4句自我介绍\n"
            "- summary: string，2-4句综合概述\n"
            "- education: string[]，教育经历数组\n"
            "- experience: string[]，工作经历数组\n"
            "- projects: string[]，项目经历数组\n"
            "- awards: string[]，获奖/证书数组\n"
            "- target_position: string，求职意向\n"
            "- skills: string[]，技能清单\n\n"
            "【重要】只提取实际存在的信息，找不到则返回空字符串或空数组。\n\n"
            f"简历文本:\n{resume_text[:8000]}"
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            result = await self.chat_json(messages)
        except Exception:
            return dict(_DEFAULT_PARSED_RESUME)

        output: dict[str, Any] = {
            "name": str(result.get("name") or "").strip(),
            "gender": str(result.get("gender") or "").strip(),
            "major": str(result.get("major") or "").strip(),
            "education_level": str(result.get("education_level") or "").strip(),
            "self_introduction": str(result.get("self_introduction") or "").strip(),
            "summary": str(result.get("summary") or "").strip(),
            "education": _normalize_list(result.get("education")),
            "experience": _normalize_list(result.get("experience")),
            "projects": _normalize_list(result.get("projects")),
            "awards": _normalize_list(result.get("awards")),
            "target_position": str(result.get("target_position") or "").strip(),
            "skills": _normalize_list(result.get("skills")),
        }

        if not output["summary"]:
            output["summary"] = _DEFAULT_PARSED_RESUME["summary"]
        if not output["self_introduction"]:
            output["self_introduction"] = output["summary"]

        return output


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list):
        return []

    output: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            output.append(text)
    return output

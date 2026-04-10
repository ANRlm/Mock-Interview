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

    SYSTEM_PROMPT = (
        "将简历内容提炼为 JSON，字段包含 name、gender、major、education_level、"
        "self_introduction、summary、education、experience、projects、awards、"
        "target_position、skills。"
    )

    async def structure_resume(self, resume_text: str) -> dict[str, Any]:
        prompt = (
            "请从以下简历文本中提取结构化信息，并严格返回 JSON。\n"
            "字段要求:\n"
            "- name: string\n"
            "- gender: string\n"
            "- major: string\n"
            "- education_level: string\n"
            "- self_introduction: string，2-4 句\n"
            "- summary: string，2-4 句概述候选人背景\n"
            "- education: string[]\n"
            "- experience: string[]\n"
            "- projects: string[]\n"
            "- awards: string[]\n"
            "- target_position: string\n"
            "- skills: string[]\n"
            "如果某字段缺失请返回空数组或空字符串，不要补造不存在的事实。\n\n"
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

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("自我评价", "个人简介", "个人总结", "summary", "profile"),
    "education": ("教育经历", "教育背景", "学历", "education"),
    "experience": (
        "工作经历",
        "工作经验",
        "实习经历",
        "experience",
        "employment",
    ),
    "projects": ("项目经历", "项目经验", "project", "projects"),
    "skills": ("专业技能", "技能", "技术栈", "skill", "skills"),
}

_MAX_SECTION_ITEMS = 6
_MAX_SUMMARY_LENGTH = 500
_DEFAULT_SUMMARY = "简历已上传，暂未解析。"


def read_resume_text(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""

    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if suffix != ".pdf":
        return ""

    try:
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            return "\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception:
        return ""


def parse_resume_text(text: str) -> dict[str, Any]:
    cleaned_text = _clean_text(text)
    if not cleaned_text:
        return _empty_resume(_DEFAULT_SUMMARY)

    sections: dict[str, list[str]] = {
        "education": [],
        "experience": [],
        "projects": [],
        "skills": [],
    }
    summary_lines: list[str] = []
    lead_lines: list[str] = []
    current_section: str | None = None

    for raw_line in cleaned_text.splitlines():
        line = _clean_line(raw_line)
        if not line:
            continue

        detected = _detect_section(line)
        if detected:
            current_section = detected
            inline = _extract_inline_content(line)
            if inline:
                if current_section == "summary":
                    _append_unique(summary_lines, inline)
                elif current_section in sections:
                    _append_unique(sections[current_section], inline)
            continue

        if current_section == "summary":
            _append_unique(summary_lines, line)
            continue

        if current_section in sections:
            _append_unique(sections[current_section], line)
            continue

        _append_unique(lead_lines, line)

    summary = _build_summary(cleaned_text, summary_lines, lead_lines)
    return {
        "summary": summary,
        "education": sections["education"][:_MAX_SECTION_ITEMS],
        "experience": sections["experience"][:_MAX_SECTION_ITEMS],
        "projects": sections["projects"][:_MAX_SECTION_ITEMS],
        "skills": sections["skills"][:_MAX_SECTION_ITEMS],
    }


def parse_resume(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return _empty_resume("简历文件不存在")

    text = read_resume_text(path)
    if not text.strip():
        return _empty_resume(_DEFAULT_SUMMARY)

    return parse_resume_text(text)


def build_resume_prompt(parsed: dict[str, Any] | None) -> str:
    if not parsed:
        return "暂无简历"

    summary = str(parsed.get("summary") or "").strip()
    projects = _normalize_items(parsed.get("projects"))
    skills = _normalize_items(parsed.get("skills"))

    parts: list[str] = []
    if summary:
        parts.append(summary)
    if projects:
        parts.append("项目经历: " + "；".join(projects[:3]))
    if skills:
        parts.append("核心技能: " + "、".join(skills[:6]))

    return "\n".join(parts) or "暂无简历"


def _clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _clean_line(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    cleaned = cleaned.strip("-•·\t ")
    return cleaned


def _normalize_heading(value: str) -> str:
    compact = value.lower()
    compact = re.sub(r"[\s：:()（）\[\]【】|/\\-]+", "", compact)
    return compact


def _detect_section(line: str) -> str | None:
    heading = _normalize_heading(line)
    if not heading or len(heading) > 30:
        return None

    for section, aliases in _SECTION_ALIASES.items():
        for alias in aliases:
            if _normalize_heading(alias) in heading:
                return section
    return None


def _extract_inline_content(line: str) -> str:
    if ":" in line:
        return line.split(":", 1)[1].strip()
    if "：" in line:
        return line.split("：", 1)[1].strip()
    return ""


def _append_unique(bucket: list[str], value: str) -> None:
    cleaned = _clean_line(value)
    if not cleaned:
        return
    if len(cleaned) > 180:
        cleaned = cleaned[:180]
    if cleaned not in bucket:
        bucket.append(cleaned)


def _build_summary(
    full_text: str,
    summary_lines: list[str],
    lead_lines: list[str],
) -> str:
    if summary_lines:
        summary = "；".join(summary_lines[:3])
    elif lead_lines:
        summary = "；".join(lead_lines[:3])
    else:
        summary = full_text.replace("\n", " ")

    summary = re.sub(r"\s+", " ", summary).strip()
    if not summary:
        return _DEFAULT_SUMMARY
    return summary[:_MAX_SUMMARY_LENGTH]


def _normalize_items(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [value]
    else:
        return []

    output: list[str] = []
    for item in items:
        text = _clean_line(str(item))
        if not text or text in output:
            continue
        output.append(text)
    return output


def _empty_resume(summary: str) -> dict[str, Any]:
    return {
        "summary": summary,
        "education": [],
        "experience": [],
        "projects": [],
        "skills": [],
    }

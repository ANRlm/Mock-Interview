from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

_EN_LETTER_RE = re.compile(r"[A-Za-z]")
_EN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-+/.]*")
_MD_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((?:https?://[^)]+)\)")
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((?:https?://[^)]+)\)")
_MD_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
_URL_RE = re.compile(r"https?://\S+")
_EN_HEAVY_SPLIT_RE = re.compile(r"([A-Za-z]{2,}\s*[，,。；;、]\s*[A-Za-z]{2,})")

_LETTER_ZH = {
    "A": "诶",
    "B": "比",
    "C": "西",
    "D": "迪",
    "E": "伊",
    "F": "艾弗",
    "G": "吉",
    "H": "艾尺",
    "I": "艾",
    "J": "杰",
    "K": "开",
    "L": "艾勒",
    "M": "艾姆",
    "N": "艾恩",
    "O": "欧",
    "P": "屁",
    "Q": "丘",
    "R": "阿尔",
    "S": "艾丝",
    "T": "提",
    "U": "优",
    "V": "维",
    "W": "达布流",
    "X": "艾克斯",
    "Y": "外",
    "Z": "贼德",
}


class TTSTextNormalizer:
    def __init__(self) -> None:
        self._lexicon_path = Path(settings.TTS_LEXICON_PATH)
        self._lexicon_mtime = 0.0
        self._exact_map: dict[str, str] = {}
        self._exact_rules: list[tuple[re.Pattern[str], str]] = []
        self._regex_rules: list[tuple[re.Pattern[str], str]] = []

    def normalize(self, text: str, *, fallback: str = "请继续。") -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return fallback

        self._reload_lexicon_if_needed()

        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        if settings.TTS_ENABLE_MARKDOWN_CLEAN:
            cleaned = _MD_CODE_BLOCK_RE.sub(" ", cleaned)
            cleaned = _MD_IMAGE_RE.sub(r"\1", cleaned)
            cleaned = _MD_LINK_RE.sub(r"\1", cleaned)
            cleaned = _MD_INLINE_CODE_RE.sub(r"\1", cleaned)
            cleaned = _URL_RE.sub(" ", cleaned)
            cleaned = re.sub(r"(^|\n)\s{0,3}#{1,6}\s*", r"\1", cleaned)
            cleaned = re.sub(r"(^|\n)\s*>\s*", r"\1", cleaned)
            cleaned = re.sub(r"(^|\n)\s*(?:[-*+]|\d+\.)\s+", r"\1", cleaned)

        cleaned = cleaned.replace("|", " ")
        cleaned = cleaned.replace("*", "")
        cleaned = cleaned.replace("_", "")
        cleaned = cleaned.replace("~", "")
        cleaned = cleaned.replace("\n", "。")
        cleaned = re.sub(r"[\[\]{}<>]+", " ", cleaned)
        cleaned = re.sub(r"\s*[:：]\s*", "，", cleaned)

        for pattern, replacement in self._exact_rules:
            cleaned = pattern.sub(replacement, cleaned)

        for pattern, replacement in self._regex_rules:
            cleaned = pattern.sub(replacement, cleaned)

        cleaned = re.sub(r"(?<=[A-Za-z0-9])(?:[._/\-])(?=[A-Za-z0-9])", " ", cleaned)

        def _replace_word(match: re.Match[str]) -> str:
            token = match.group(0)
            mapped = self._exact_map.get(token.lower())
            if mapped:
                return mapped
            if not settings.TTS_ENABLE_EN_TO_ZH:
                return token
            upper = token.upper()
            parts = []
            for ch in upper:
                if "A" <= ch <= "Z":
                    parts.append(_LETTER_ZH.get(ch, ch))
                elif ch.isdigit():
                    parts.append(ch)
            if not parts:
                return token
            return " ".join(parts)

        cleaned = _EN_WORD_RE.sub(_replace_word, cleaned)

        cleaned = _EN_HEAVY_SPLIT_RE.sub(
            lambda m: m.group(1).replace("，", "。"), cleaned
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r"([。！？]){2,}", r"\1", cleaned)
        cleaned = re.sub(r"([，,]){2,}", r"\1", cleaned)
        cleaned = cleaned.strip("，,。")

        if settings.TTS_ENABLE_AUTO_PUNCTUATION and cleaned:
            cleaned = f"{cleaned}。"

        if not cleaned:
            return fallback
        return cleaned

    def _reload_lexicon_if_needed(self) -> None:
        try:
            stat = self._lexicon_path.stat()
        except FileNotFoundError:
            return
        except Exception as exc:
            logger.warning("TTS lexicon stat failed: %s", exc)
            return

        if stat.st_mtime <= self._lexicon_mtime:
            return

        try:
            data = json.loads(self._lexicon_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("TTS lexicon load failed: %s", exc)
            return

        exact_raw = data.get("exact") if isinstance(data, dict) else {}
        regex_raw = data.get("regex") if isinstance(data, dict) else []

        exact: dict[str, str] = {}
        if isinstance(exact_raw, dict):
            for key, value in exact_raw.items():
                k = str(key).strip().lower()
                v = str(value).strip()
                if k and v:
                    exact[k] = v

        exact_rules: list[tuple[re.Pattern[str], str]] = []
        for key, replacement in exact.items():
            pattern = self._build_exact_pattern(key)
            if pattern is not None:
                exact_rules.append((pattern, replacement))

        regex_rules: list[tuple[re.Pattern[str], str]] = []
        if isinstance(regex_raw, list):
            for item in regex_raw:
                if not isinstance(item, dict):
                    continue
                pattern = str(item.get("pattern", "")).strip()
                replacement = str(item.get("replacement", "")).strip()
                if not pattern or not replacement:
                    continue
                try:
                    regex_rules.append(
                        (re.compile(pattern, flags=re.IGNORECASE), replacement)
                    )
                except re.error:
                    continue

        self._exact_map = exact
        self._exact_rules = exact_rules
        self._regex_rules = regex_rules
        self._lexicon_mtime = stat.st_mtime
        logger.info(
            "TTS lexicon loaded path=%s exact=%s exact_rules=%s regex=%s",
            self._lexicon_path,
            len(self._exact_map),
            len(self._exact_rules),
            len(self._regex_rules),
        )

    def force_reload(self) -> None:
        self._lexicon_mtime = 0.0
        self._reload_lexicon_if_needed()

    def _build_exact_pattern(self, key: str) -> re.Pattern[str] | None:
        tokens = [part for part in re.split(r"[\s._/\-]+", key) if part]
        if not tokens:
            return None

        escaped_tokens = [re.escape(part) for part in tokens]
        if len(escaped_tokens) == 1:
            raw = rf"\b{escaped_tokens[0]}\b"
        else:
            joiner = r"[\s._/\-]*"
            raw = rf"\b{joiner.join(escaped_tokens)}\b"

        try:
            return re.compile(raw, flags=re.IGNORECASE)
        except re.error:
            return None


tts_text_normalizer = TTSTextNormalizer()

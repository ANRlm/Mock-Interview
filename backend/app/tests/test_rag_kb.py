from pathlib import Path

import pytest

from app.config import settings


class TestKnowledgeBaseLoading:
    JOB_ROLES = ["teacher", "doctor", "lawyer", "programmer"]
    MIN_MARKDOWN_FILES = 3
    MIN_FILE_CONTENT_LENGTH = 100

    @pytest.fixture
    def kb_base_dir(self) -> Path:
        return Path(settings.KNOWLEDGE_BASE_DIR)

    def _get_role_dir(self, kb_base_dir: Path, role: str) -> Path:
        return kb_base_dir / role

    def _get_markdown_files(self, role_dir: Path) -> list[Path]:
        return sorted(role_dir.glob("*.md"))

    def test_kb_directory_exists_for_all_roles(self, kb_base_dir: Path) -> None:
        for role in self.JOB_ROLES:
            role_dir = self._get_role_dir(kb_base_dir, role)
            assert role_dir.exists(), f"KB directory for role '{role}' does not exist at {role_dir}"
            assert role_dir.is_dir(), f"KB path for role '{role}' is not a directory"

    def test_each_role_has_minimum_markdown_files(self, kb_base_dir: Path) -> None:
        for role in self.JOB_ROLES:
            role_dir = self._get_role_dir(kb_base_dir, role)
            md_files = self._get_markdown_files(role_dir)
            assert len(md_files) >= self.MIN_MARKDOWN_FILES, (
                f"Role '{role}' has {len(md_files)} markdown files, "
                f"expected at least {self.MIN_MARKDOWN_FILES}"
            )

    def test_each_markdown_file_has_content(self, kb_base_dir: Path) -> None:
        for role in self.JOB_ROLES:
            role_dir = self._get_role_dir(kb_base_dir, role)
            md_files = self._get_markdown_files(role_dir)
            for md_file in md_files:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                assert len(content) > self.MIN_FILE_CONTENT_LENGTH, (
                    f"File '{md_file.name}' in role '{role}' has only {len(content)} chars, "
                    f"expected more than {self.MIN_FILE_CONTENT_LENGTH}"
                )

    def test_each_markdown_file_contains_keywords(self, kb_base_dir: Path) -> None:
        for role in self.JOB_ROLES:
            role_dir = self._get_role_dir(kb_base_dir, role)
            md_files = self._get_markdown_files(role_dir)
            for md_file in md_files:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                assert len(content.strip()) > 0, f"File '{md_file.name}' in role '{role}' is empty"
                keywords = ["面试", "问题", "角色"]
                matched = any(keyword in content for keyword in keywords)
                assert matched, (
                    f"File '{md_file.name}' in role '{role}' does not contain "
                    f"any expected keywords {keywords}"
                )

    def test_search_returns_non_empty_results(self, kb_base_dir: Path) -> None:
        for role in self.JOB_ROLES:
            role_dir = self._get_role_dir(kb_base_dir, role)
            md_files = self._get_markdown_files(role_dir)
            all_content: list[str] = []
            for md_file in md_files:
                content = md_file.read_text(encoding="utf-8", errors="ignore").strip()
                if content:
                    all_content.append(content)
            assert len(all_content) >= self.MIN_MARKDOWN_FILES, (
                f"Role '{role}' has only {len(all_content)} non-empty files, "
                f"expected at least {self.MIN_MARKDOWN_FILES}"
            )

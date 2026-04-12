from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.llm_config import LLMRuntimeConfig

ProfileName = Literal["local", "cloud"]


@dataclass(slots=True)
class LLMProfile:
    name: ProfileName
    label: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int
    disable_thinking: bool
    enabled: bool = True


def profile_to_dict(profile: LLMProfile) -> dict:
    return {
        "name": profile.name,
        "label": profile.label,
        "base_url": profile.base_url,
        "model": profile.model,
        "timeout_seconds": profile.timeout_seconds,
        "disable_thinking": profile.disable_thinking,
        "enabled": profile.enabled,
    }


class LLMProfileService:
    _TASK_PROFILE_KEYS: dict[str, str] = {
        "resume": "LLM_RESUME_PROFILE",
        "interview": "LLM_INTERVIEW_PROFILE",
        "evaluation": "LLM_EVALUATION_PROFILE",
        "verifier": "LLM_VERIFIER_PROFILE",
    }

    _TASK_MODEL_KEYS: dict[str, str] = {
        "resume": "LLM_RESUME_MODEL",
        "interview": "LLM_INTERVIEW_MODEL",
        "evaluation": "LLM_EVALUATION_MODEL",
        "verifier": "LLM_VERIFIER_MODEL",
    }

    _VALID_ROUTING_STRATEGIES = {"low_latency", "balanced", "quality"}

    _STRATEGY_PRESETS: dict[str, dict[str, dict[str, str]]] = {
        "low_latency": {
            "resume": {"profile": "local", "model": ""},
            "interview": {"profile": "local", "model": ""},
            "evaluation": {"profile": "local", "model": ""},
            "verifier": {"profile": "local", "model": ""},
        },
        "balanced": {
            "resume": {"profile": "local", "model": ""},
            "interview": {"profile": "local", "model": ""},
            "evaluation": {"profile": "cloud", "model": ""},
            "verifier": {"profile": "local", "model": ""},
        },
        "quality": {
            "resume": {"profile": "cloud", "model": ""},
            "interview": {"profile": "cloud", "model": ""},
            "evaluation": {"profile": "cloud", "model": ""},
            "verifier": {"profile": "cloud", "model": ""},
        },
    }

    def _base_profiles(self) -> dict[ProfileName, LLMProfile]:
        profiles: dict[ProfileName, LLMProfile] = {
            "local": LLMProfile(
                name="local",
                label="本地 Ollama",
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                disable_thinking=settings.LLM_DISABLE_THINKING,
                enabled=True,
            ),
            "cloud": LLMProfile(
                name="cloud",
                label="云端模型",
                base_url=settings.CLOUD_LLM_BASE_URL,
                api_key=settings.CLOUD_LLM_API_KEY,
                model=settings.CLOUD_LLM_MODEL,
                timeout_seconds=settings.CLOUD_LLM_TIMEOUT_SECONDS,
                disable_thinking=settings.CLOUD_LLM_DISABLE_THINKING,
                enabled=settings.CLOUD_LLM_ENABLED
                and bool(settings.CLOUD_LLM_BASE_URL.strip())
                and bool(settings.CLOUD_LLM_MODEL.strip()),
            ),
        }
        return profiles

    async def ensure_runtime_config(self, db: AsyncSession) -> LLMRuntimeConfig:
        await self._ensure_schema_columns(db)
        config = await db.get(LLMRuntimeConfig, 1)
        if config is None:
            config = LLMRuntimeConfig(
                id=1,
                active_profile=(
                    settings.LLM_DEFAULT_PROFILE
                    if settings.LLM_DEFAULT_PROFILE in {"local", "cloud"}
                    else "local"
                ),
                active_model=None,
                disable_thinking_override=None,
                routing_strategy=self._normalize_strategy(
                    settings.LLM_ROUTING_STRATEGY
                ),
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
        else:
            expected = self._normalize_strategy(config.routing_strategy)
            if expected != config.routing_strategy:
                config.routing_strategy = expected
                await db.commit()
                await db.refresh(config)
        return config

    async def _ensure_schema_columns(self, db: AsyncSession) -> None:
        result = await db.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'llm_runtime_config'"
            )
        )
        columns = {str(row[0]) for row in result.fetchall()}

        if "routing_strategy" not in columns:
            await db.execute(
                text(
                    "ALTER TABLE llm_runtime_config "
                    "ADD COLUMN routing_strategy VARCHAR(24) NOT NULL DEFAULT 'balanced'"
                )
            )
            await db.commit()

    async def get_runtime_profile(self, db: AsyncSession) -> LLMProfile:
        config = await self.ensure_runtime_config(db)
        profiles = self._base_profiles()

        preferred = (
            config.active_profile if config.active_profile in profiles else "local"
        )
        profile = profiles[preferred]
        if not profile.enabled:
            profile = profiles["local"]

        if config.active_model and config.active_model.strip():
            profile = replace(profile, model=config.active_model.strip())

        if config.disable_thinking_override is not None:
            profile = replace(
                profile,
                disable_thinking=bool(config.disable_thinking_override),
            )

        return profile

    def resolve_task_profile(
        self,
        runtime_profile: LLMProfile,
        task: str,
        *,
        strategy_override: str | None = None,
    ) -> LLMProfile:
        task_key = (task or "").strip().lower()
        if not task_key:
            return runtime_profile

        strategy = self._normalize_strategy(
            strategy_override or settings.LLM_ROUTING_STRATEGY
        )
        preset = self._STRATEGY_PRESETS.get(strategy, {}).get(task_key, {})

        task_profile_raw = str(
            getattr(self._settings_obj(), self._TASK_PROFILE_KEYS.get(task_key, ""), "")
        ).strip()
        task_model_raw = str(
            getattr(self._settings_obj(), self._TASK_MODEL_KEYS.get(task_key, ""), "")
        ).strip()

        if not task_profile_raw:
            task_profile_raw = str(preset.get("profile") or "")
        if not task_model_raw:
            task_model_raw = str(preset.get("model") or "")

        profile = runtime_profile
        if task_profile_raw in {"local", "cloud"}:
            base_profiles = self._base_profiles()
            candidate = base_profiles.get(task_profile_raw)
            if candidate and candidate.enabled:
                profile = candidate

        if task_model_raw:
            profile = replace(profile, model=task_model_raw)

        return profile

    def _settings_obj(self):
        return settings

    async def list_profiles(self, db: AsyncSession) -> dict:
        config = await self.ensure_runtime_config(db)
        profiles = self._base_profiles()

        preferred = (
            config.active_profile if config.active_profile in profiles else "local"
        )
        active_runtime = profiles[preferred]
        if not active_runtime.enabled:
            active_runtime = profiles["local"]
        if config.active_model and config.active_model.strip():
            active_runtime = replace(active_runtime, model=config.active_model.strip())
        if config.disable_thinking_override is not None:
            active_runtime = replace(
                active_runtime,
                disable_thinking=bool(config.disable_thinking_override),
            )

        options = []
        for profile in profiles.values():
            options.append(
                {
                    "name": profile.name,
                    "label": profile.label,
                    "enabled": profile.enabled,
                    "default_model": profile.model,
                    "default_disable_thinking": profile.disable_thinking,
                    "using_now": config.active_profile == profile.name,
                }
            )

        return {
            "active_profile": config.active_profile,
            "active_model": config.active_model,
            "disable_thinking_override": config.disable_thinking_override,
            "routing_strategy": config.routing_strategy,
            "routing_strategies": [
                {
                    "name": "low_latency",
                    "label": "低延迟",
                    "description": "全部任务优先本地低时延模型",
                },
                {
                    "name": "balanced",
                    "label": "平衡",
                    "description": "面试实时链路本地，评估可优先云端",
                },
                {
                    "name": "quality",
                    "label": "高质量",
                    "description": "优先云端高质量模型（若可用）",
                },
            ],
            "active_runtime": profile_to_dict(active_runtime),
            "task_routes": self._task_routes_snapshot(config, profiles),
            "profiles": options,
        }

    async def update_runtime_profile(
        self,
        db: AsyncSession,
        *,
        profile_name: str,
        model: str | None,
        disable_thinking: bool | None,
        routing_strategy: str | None,
    ) -> dict:
        if profile_name not in {"local", "cloud"}:
            raise ValueError("profile must be local or cloud")

        config = await self.ensure_runtime_config(db)
        base_profiles = self._base_profiles()
        candidate = base_profiles[profile_name]  # type: ignore[index]
        if not candidate.enabled:
            raise ValueError("selected profile is not enabled")

        config.active_profile = profile_name
        config.active_model = model.strip() if model and model.strip() else None
        config.disable_thinking_override = disable_thinking
        if routing_strategy is not None:
            config.routing_strategy = self._normalize_strategy(routing_strategy)
        await db.commit()
        await db.refresh(config)
        return await self.list_profiles(db)

    def _normalize_strategy(self, value: str | None) -> str:
        candidate = (value or "").strip().lower()
        if candidate in self._VALID_ROUTING_STRATEGIES:
            return candidate
        return "balanced"

    def _task_routes_snapshot(
        self,
        config: LLMRuntimeConfig,
        base_profiles: dict[ProfileName, LLMProfile],
    ) -> dict[str, dict]:
        snapshot: dict[str, dict] = {}
        strategy = self._normalize_strategy(config.routing_strategy)

        runtime_profile_name = (
            config.active_profile if config.active_profile in base_profiles else "local"
        )
        runtime_profile = base_profiles[runtime_profile_name]
        if not runtime_profile.enabled:
            runtime_profile = base_profiles["local"]

        if config.active_model and config.active_model.strip():
            runtime_profile = replace(
                runtime_profile, model=config.active_model.strip()
            )
        if config.disable_thinking_override is not None:
            runtime_profile = replace(
                runtime_profile,
                disable_thinking=bool(config.disable_thinking_override),
            )

        for task in self._TASK_PROFILE_KEYS:
            profile = self.resolve_task_profile(
                runtime_profile, task, strategy_override=strategy
            )
            snapshot[task] = {
                "profile": profile.name,
                "model": profile.model,
                "disable_thinking": profile.disable_thinking,
                "base_url": profile.base_url,
            }

        return snapshot


llm_profile_service = LLMProfileService()

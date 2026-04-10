from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

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
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
        return config

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
            "active_runtime": profile_to_dict(active_runtime),
            "profiles": options,
        }

    async def update_runtime_profile(
        self,
        db: AsyncSession,
        *,
        profile_name: str,
        model: str | None,
        disable_thinking: bool | None,
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
        await db.commit()
        await db.refresh(config)
        return await self.list_profiles(db)


llm_profile_service = LLMProfileService()

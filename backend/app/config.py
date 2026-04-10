from __future__ import annotations

import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Mock Interview API"
    API_V1_PREFIX: str = "/api"

    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "ollama"
    LLM_MODEL: str = "qwen3.5:2b"
    LLM_TIMEOUT_SECONDS: int = 90
    LLM_DISABLE_THINKING: bool = True
    LLM_DEFAULT_PROFILE: str = "local"

    LLM_RESUME_PROFILE: str = ""
    LLM_RESUME_MODEL: str = ""
    LLM_INTERVIEW_PROFILE: str = ""
    LLM_INTERVIEW_MODEL: str = ""
    LLM_EVALUATION_PROFILE: str = ""
    LLM_EVALUATION_MODEL: str = ""
    LLM_VERIFIER_PROFILE: str = ""
    LLM_VERIFIER_MODEL: str = ""
    LLM_ROUTING_STRATEGY: str = "balanced"

    CLOUD_LLM_ENABLED: bool = False
    CLOUD_LLM_BASE_URL: str = ""
    CLOUD_LLM_API_KEY: str = ""
    CLOUD_LLM_MODEL: str = ""
    CLOUD_LLM_TIMEOUT_SECONDS: int = 90
    CLOUD_LLM_DISABLE_THINKING: bool = False

    STT_BACKEND: str = "funasr-http"
    FUNASR_BASE_URL: str = "http://127.0.0.1:10095"
    FUNASR_HEALTH_PATH: str = "/healthz"
    FUNASR_TIMEOUT_SECONDS: int = 20
    FUNASR_USE_ITN: bool = True
    FUNASR_EXTRA_PAYLOAD: str = "{}"

    TTS_BACKEND: str = "cosyvoice2-http"
    COSYVOICE_BASE_URL: str = "http://127.0.0.1:50000"
    COSYVOICE_TTS_PATH: str = "/inference_sft"
    COSYVOICE_HEALTH_PATH: str = "/openapi.json"
    COSYVOICE_TIMEOUT_SECONDS: int = 25
    COSYVOICE_VOICE: str = "default_zh"
    COSYVOICE_SAMPLE_RATE: int = 22050
    COSYVOICE_EXTRA_PAYLOAD: str = "{}"

    TTS_CACHE_DIR: str = "./uploads/tts_cache"

    DATABASE_URL: str = "sqlite+aiosqlite:///./mock_interview.db"

    CORS_ORIGINS: str = "http://localhost:5173"
    UPLOAD_DIR: str = "./uploads"
    CHROMA_DB_DIR: str = "./chroma_db"
    KNOWLEDGE_BASE_DIR: str = "./knowledge_base"
    VISION_SAMPLE_INTERVAL: int = 5

    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    @property
    def cors_origins(self) -> list[str]:
        text = self.CORS_ORIGINS.strip()
        if not text:
            return []
        if text.startswith("["):
            parsed = json.loads(text)
            if not isinstance(parsed, list):
                raise ValueError("CORS_ORIGINS JSON must be a list")
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in text.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

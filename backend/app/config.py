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

    JWT_SECRET: str = "change-this-in-production-use-env-var"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "ollama"
    LLM_MODEL: str = "qwen3:14b"
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
    LLM_INTERVIEW_RAG_MAX_CHARS: int = 520
    LLM_INTERVIEW_RAG_CHUNK_MAX_CHARS: int = 220

    CLOUD_LLM_ENABLED: bool = False
    CLOUD_LLM_BASE_URL: str = ""
    CLOUD_LLM_API_KEY: str = ""
    CLOUD_LLM_MODEL: str = ""
    CLOUD_LLM_TIMEOUT_SECONDS: int = 90
    CLOUD_LLM_DISABLE_THINKING: bool = False

    STT_BACKEND: str = "paraformer-streaming"
    FUNASR_BASE_URL: str = "http://127.0.0.1:10095"
    FUNASR_HEALTH_PATH: str = "/healthz"
    FUNASR_TIMEOUT_SECONDS: int = 20
    FUNASR_USE_ITN: bool = True
    FUNASR_EXTRA_PAYLOAD: str = "{}"

    SENSEVOICE_BASE_URL: str = "http://127.0.0.1:5001"
    SENSEVOICE_API_KEY: str = ""
    SENSEVOICE_TIMEOUT_SECONDS: int = 20

    VAD_MODEL: str = "silero"
    VAD_HANGOVER_MS: int = 300
    VAD_THRESHOLD: float = 0.5

    PARAFORMER_BASE_URL: str = "http://127.0.0.1:10095"
    PARAFORMER_CHUNK_SIZE_MS: int = 600

    TTS_BACKEND: str = "qwen3-tts"
    COSYVOICE_BASE_URL: str = "http://127.0.0.1:50000"
    COSYVOICE_TTS_PATH: str = "/inference_sft"
    COSYVOICE_HEALTH_PATH: str = "/openapi.json"
    COSYVOICE_TIMEOUT_SECONDS: int = 25
    COSYVOICE_VOICE: str = "default_zh"
    COSYVOICE_MODE: str = "sft"
    COSYVOICE_INSTRUCT_TEXT: str = (
        "用甜美、温柔、自然、清晰的中文女声播报，语气亲切，节奏流畅。"
    )
    COSYVOICE_SAMPLE_RATE: int = 22050
    COSYVOICE_EXTRA_PAYLOAD: str = "{}"
    COSYVOICE_SPEED: float = 1.6
    COSYVOICE_SEED: int = 3407
    COSYVOICE_WARM_TIMEOUT_SECONDS: float = 1.2
    COSYVOICE_WARM_KEEPALIVE_SECONDS: float = 90.0
    TTS_LEXICON_PATH: str = "./knowledge_base/tts_lexicon.json"
    TTS_ENABLE_EN_TO_ZH: bool = True
    TTS_ENABLE_MARKDOWN_CLEAN: bool = True
    TTS_ENABLE_AUTO_PUNCTUATION: bool = True
    TTS_SENTENCE_MAX_CHARS: int = 120
    TTS_SENTENCE_SOFT_CHARS: int = 64
    TTS_REQUEST_TIMEOUT_SECONDS: float = 20.0
    TTS_FIRST_CHUNK_TIMEOUT_SECONDS: float = 5.0
    TTS_HEDGE_ENABLED: bool = True
    TTS_HEDGE_DELAY_SECONDS: float = 0.55
    TTS_HEDGE_MAX_RACERS: int = 2

    # Latency budgets (NEW)
    STT_MAX_LATENCY_MS: int = 600
    TTS_MAX_LATENCY_MS: int = 200
    E2E_MAX_LATENCY_MS: int = 2000

    # Echo cancellation (NEW)
    ECHO_CANCELLATION_ENABLED: bool = True

    # TTS routing (NEW)
    TTS_PRIMARY: str = "qwen3-tts"
    TTS_FALLBACK: str = "f5-tts"
    TTS_LAST_RESORT: str = "cosyvoice2"

    QWEN_TTS_BASE_URL: str = "http://127.0.0.1:50001"
    QWEN_TTS_MODEL: str = "qwen3-tts"
    QWEN_TTS_TIMEOUT_SECONDS: int = 20

    TTS_CACHE_DIR: str = "./uploads/tts_cache"

    DATABASE_URL: str = "sqlite+aiosqlite:///./mock_interview.db"

    CORS_ORIGINS: str = "http://localhost:5173"
    CORS_ALLOW_ALL: bool = True
    UPLOAD_DIR: str = "./uploads"
    CHROMA_DB_DIR: str = "./chroma_db"
    KNOWLEDGE_BASE_DIR: str = "./knowledge_base"
    VISION_SAMPLE_INTERVAL: int = 5

    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    # VRAM budget (RTX 5080 16GB)
    VRAM_BUDGET_MB: int = 16384
    VRAM_LLM_MB: int = 12288
    VRAM_TTS_MB: int = 2048
    VRAM_STT_MB: int = 1024

    # Concurrency settings
    MAX_STT_WORKERS: int = 2
    MAX_TTS_WORKERS: int = 2
    MAX_LLM_STREAMS: int = 4
    MAX_CONCURRENT_SESSIONS: int = 4

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

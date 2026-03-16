from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # LLM Models
    LLM_MODEL: str = "anthropic/claude-sonnet-4-6"  # Gerador principal
    LLM_MODEL_FAST: str = "anthropic/claude-haiku-4-5"  # Ajustador (econômico)
    LLM_MODEL_SEARCH: str = "perplexity/sonar-pro"  # Pesquisador (web search)

    # Database (no default — must be set via env)
    DATABASE_URL: str

    # Redis (no default — must be set via env)
    REDIS_URL: str

    # Storage
    STORAGE_PATH: str = "/app/storage"

    # Pipeline
    MAX_ITERATIONS: int = 3
    QUALITY_THRESHOLD: int = 70

    # Gotenberg (PDF generation)
    GOTENBERG_URL: str = "http://gotenberg:3000"

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Security
    API_SECRET_KEY: Optional[str] = None
    DEBUG: bool = False


settings = Settings()


def get_settings() -> Settings:
    return settings

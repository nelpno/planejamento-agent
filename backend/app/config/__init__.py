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
    LLM_MODEL: str = "anthropic/claude-sonnet-4"
    LLM_MODEL_FAST: str = "anthropic/claude-haiku-4.5"
    LLM_MODEL_SEARCH: str = "perplexity/sonar-pro"  # Web search nativo

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://planner:password@postgres:5432/planejamento_agent"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

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

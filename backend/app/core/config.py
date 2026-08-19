from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "AI Email Automation Platform"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./dev.db"

    # Redis / queue
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@example.com"
    smtp_from_name: str = "Email Platform"
    smtp_use_tls: bool = True

    # LLM — Groq (OpenAI-compatible API)
    groq_api_key: str = ""
    llm_api_key: str = ""  # legacy alias; groq_api_key wins if both set
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"

    @property
    def effective_llm_api_key(self) -> str:
        return self.groq_api_key or self.llm_api_key

    # Tracking / public URLs
    public_api_url: str = "http://localhost:8000"

    # Observability
    sentry_dsn: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

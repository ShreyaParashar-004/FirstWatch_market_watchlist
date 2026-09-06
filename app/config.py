from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite:///./watch.db"
    access_token_expire_minutes: int = 60 * 24 * 7

    market_data_provider: str = "yahoo"
    information_provider: str = "google_news"
    ai_provider: str = "mock"

    change_threshold_pct: float = 2.0
    stale_after_seconds: int = 900
    information_cache_hours: int = 24
    signal_lookback_hours: int = 72

    cors_origins: str = "*"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_base_url: str = "https://api.groq.com/openai/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()

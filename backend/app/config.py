"""Central configuration. All secrets come from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./kavach.db"
    jwt_secret: str = "dev-only-change-me-please-use-32+chars"
    jwt_expire_minutes: int = 60 * 12
    cors_origins: str = "http://localhost:3000"
    max_upload_bytes: int = 5 * 1024 * 1024
    rate_limit_per_minute: int = 60

    # Optional integrations. Absent key => tool reports "unavailable" (never faked).
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    safe_browsing_api_key: str = ""
    virustotal_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()

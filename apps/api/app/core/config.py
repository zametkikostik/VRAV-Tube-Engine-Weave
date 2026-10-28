"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = Field(default="change-me-in-production-use-long-random-string")
    app_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://vrav:vrav@localhost:5432/vrav_tube"
    database_url_sync: str = "postgresql://vrav:vrav@localhost:5432/vrav_tube"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    password_hash_scheme: str = "argon2"
    algorithm: str = "HS256"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = ""
    routerai_api_key: str = ""
    routerai_base_url: str = "https://routerai.ru/api/v1"
    routerai_default_model: str = ""
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    ai_timeout_seconds: int = 120
    ai_max_retries: int = 3

    feature_white_label: bool = True
    feature_routerai: bool = True
    feature_stripe: bool = True
    feature_yookassa: bool = False

    ffmpeg_max_duration_seconds: int = 3600
    ffmpeg_max_resolution: int = 1920
    ffmpeg_sample_fps: float = 0.5
    ffmpeg_timeout_seconds: int = 300

    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @field_validator("app_secret_key")
    @classmethod
    def secret_key_strength(cls, v: str) -> str:
        if v == "change-me-in-production-use-long-random-string":
            return v
        if len(v) < 32:
            raise ValueError("APP_SECRET_KEY must be at least 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()

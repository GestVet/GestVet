from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "gestvet-api"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./gestvet.db"
    cors_allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""LABEL-X backend configuration.

All configuration comes from environment variables (optionally loaded from a
local `.env` file, never committed). Nothing here is a secret — see
`.env.example` for the full list of variables and safe local defaults.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "label-x-backend"
    app_version: str = "0.1.0"
    app_env: str = "development"
    log_level: str = "INFO"

    # Comma-separated list of allowed origins, or "*" for all (demo default).
    cors_allow_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — environment is read once per process."""

    return Settings()

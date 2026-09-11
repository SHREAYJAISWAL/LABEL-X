"""LABEL-X frontend configuration.

Env-var driven, mirrors backend/config.py's approach. No secrets — see
`.env.example`.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class FrontendSettings(BaseSettings):
    backend_url: str = "http://localhost:8000"
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_frontend_settings() -> FrontendSettings:
    return FrontendSettings()

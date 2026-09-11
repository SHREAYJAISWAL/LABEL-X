"""Database configuration.

All connection details come from environment variables (optionally via a
local `.env`, never committed) — see `.env.example`. No credentials are
hardcoded anywhere in this module or elsewhere in the codebase.

Two ways to configure the connection:

1. Set `DATABASE_URL` directly (any SQLAlchemy-compatible URL), or
2. Leave it unset and set the individual `POSTGRES_*` variables — a
   `postgresql+psycopg2://` URL is assembled from them automatically.

(1) always wins if both are present.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    database_url: str | None = Field(default=None)

    postgres_user: str = "labelx"
    postgres_password: str = "changeme"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "labelx"

    # Dimensionality of the pgvector embedding column on rule_versions.
    # Only relevant once the RAG phase picks an embedding model; the column
    # is created ahead of time so no migration is needed later.
    embedding_dim: int = 1536

    # If true, `database.init_db.init_db()` will call
    # `Base.metadata.create_all()` on startup — convenient for local/demo use.
    # Alembic migrations remain the source of truth for any shared or
    # production-like environment.
    db_auto_create: bool = False

    # Verify connections are alive before handing them out of the pool —
    # cheap insurance against stale connections after e.g. a DB restart.
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def sqlalchemy_url(self) -> str:
        """The URL actually used to create the SQLAlchemy engine."""

        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()

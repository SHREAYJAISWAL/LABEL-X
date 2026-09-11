"""Alembic environment.

Reads the database URL from `database.config.get_database_settings()`
(env vars) rather than from `alembic.ini`, so there is exactly one place
connection configuration lives, and it stays consistent with the app's own
engine (`database/session.py`).
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Registers every model on Base.metadata (see database/models/__init__.py).
import database.models  # noqa: F401
from database.base import Base
from database.config import get_database_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return get_database_settings().sqlalchemy_url


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection ('--sql' mode)."""

    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection (the normal case)."""

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

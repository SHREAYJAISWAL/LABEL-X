"""Database initialization helpers.

This module provides two independent things:

1. `check_connection()` — verify the app can actually reach PostgreSQL, with
   a clear error message if not. Safe to call from a startup hook or a CLI.
2. `init_db()` — for local/demo use only. Enables the `vector` extension
   (best-effort — a no-op if pgvector isn't installed on the server, since
   this phase does not require it to already be present) and calls
   `Base.metadata.create_all()`. In any shared or production-like
   environment, use Alembic migrations (`alembic upgrade head`) instead —
   `init_db()` does not track schema history the way Alembic does.

Run directly for a quick local sanity check:
    python -m database.init_db
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from database.base import Base
from database.session import engine

# Importing database.models registers every table on Base.metadata.
import database.models  # noqa: F401  (import for side effect)

logger = logging.getLogger(__name__)


def check_connection() -> bool:
    """Return True if a connection to the configured database succeeds.

    Never raises — logs the failure and returns False, so callers (e.g. a
    `/health` extension in a later phase) can degrade gracefully instead of
    crashing when the database is unreachable.
    """

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError as exc:
        logger.error("Database connection failed: %s", exc)
        return False


def enable_pgvector_extension() -> None:
    """Best-effort `CREATE EXTENSION IF NOT EXISTS vector`.

    Requires a Postgres server with the pgvector extension available (the
    `pgvector/pgvector` Docker image used in docker-compose ships it) and a
    role with sufficient privilege. Failures are logged, not raised — the
    rest of the schema (including the embedding column's JSON fallback, see
    `database/types.py`) still works without it.
    """

    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension enabled (or already present).")
    except (OperationalError, ProgrammingError) as exc:
        logger.warning(
            "Could not enable the pgvector extension (continuing without it): %s", exc
        )


def init_db() -> None:
    """Create all tables from the current models. Local/demo use only."""

    enable_pgvector_extension()
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema created via Base.metadata.create_all().")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | %(message)s")
    if not check_connection():
        raise SystemExit(
            "Could not connect to PostgreSQL. Check DATABASE_URL / POSTGRES_* in "
            ".env, and that the database is running (see deployment/docker-compose.yml)."
        )
    init_db()
    print("Database initialized successfully.")

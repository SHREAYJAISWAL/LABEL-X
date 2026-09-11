"""SQLAlchemy engine and session management.

`get_db()` is a generator dependency (usable with FastAPI's `Depends`, or
directly via `next(get_db())` / manual iteration in scripts) that always
closes its session, even on error. `session_scope()` is the equivalent
context-manager form for plain scripts (seeding, one-off queries) that
commits on success and rolls back on exception.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.config import get_database_settings

_settings = get_database_settings()

engine = create_engine(
    _settings.sqlalchemy_url,
    pool_pre_ping=_settings.db_pool_pre_ping,
    echo=_settings.db_echo,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI-style dependency: yields a session, always closes it."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for scripts: commits on success, rolls back on error."""

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

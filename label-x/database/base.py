"""Declarative base and shared mixins for all LABEL-X models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for every LABEL-X table."""


class UUIDPKMixin:
    """Adds a UUID primary key, generated client-side with `uuid4()`.

    Client-side generation (rather than relying on a Postgres default like
    `gen_random_uuid()`) means no extra Postgres extension is required and
    the id is available immediately after constructing the Python object,
    before it's flushed to the database.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """Adds `created_at` / `updated_at`, both maintained by the database."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

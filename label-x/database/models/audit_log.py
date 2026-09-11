"""audit_logs — append-only record of significant actions.

Covers both user actions (e.g. an inspector override) and system actions
(`user_id` null). Nothing writes to this table yet — it's provisioned ahead
of the phases (review/override, reporting) that will.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from database.models.screening import Screening
    from database.models.user import User


class AuditLog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_screening_created_at", "screening_id", "created_at"),
        Index("ix_audit_logs_user_created_at", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    screening_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("screenings.id", ondelete="SET NULL"), nullable=True
    )

    # e.g. "screening_created", "override_applied" — free text, not an enum,
    # since the set of actions will keep growing across phases.
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="audit_logs")
    screening: Mapped["Screening | None"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog id={self.id} action={self.action!r}>"

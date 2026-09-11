"""screenings — one screening run of a package against LABEL-X.

`status` tracks pipeline progress (created/processing/completed/failed).
`overall_result` is the three-state result (docs/ARCHITECTURE.md §3) once the
deterministic rule engine has produced one — nullable because this phase
does not implement the rule engine, so it stays unset for now.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin
from database.enums import ScreeningResult, ScreeningStatus

if TYPE_CHECKING:
    from database.models.audit_log import AuditLog
    from database.models.declaration import Declaration
    from database.models.image import Image
    from database.models.user import User
    from database.models.validation_result import ValidationResult


class Screening(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "screenings"
    __table_args__ = (Index("ix_screenings_status_created_at", "status", "created_at"),)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[ScreeningStatus] = mapped_column(
        Enum(ScreeningStatus, name="screening_status"),
        nullable=False,
        default=ScreeningStatus.CREATED,
        index=True,
    )
    overall_result: Mapped[ScreeningResult | None] = mapped_column(
        Enum(ScreeningResult, name="screening_result"), nullable=True
    )

    # Demo categories per docs/ARCHITECTURE.md §11 (Biscuits, Tea, Soap,
    # Cereals/Pulses, Salt) — free text for now, not an enum, since category
    # determination is a later phase and the value may start out unknown.
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="screenings")
    images: Mapped[list["Image"]] = relationship(
        back_populates="screening", cascade="all, delete-orphan"
    )
    declarations: Mapped[list["Declaration"]] = relationship(
        back_populates="screening", cascade="all, delete-orphan"
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        back_populates="screening", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="screening")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Screening id={self.id} status={self.status.value}>"

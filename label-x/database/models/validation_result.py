"""validation_results — one deterministic rule-engine finding.

Per docs/ARCHITECTURE.md §3, `result` may only ever be one of the three
states in `ScreeningResult` — never a numeric score. This phase defines the
table only; no rule engine exists yet to populate it.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin
from database.enums import ScreeningResult

if TYPE_CHECKING:
    from database.models.declaration import Declaration
    from database.models.evidence import Evidence
    from database.models.rule_version import RuleVersion
    from database.models.screening import Screening


class ValidationResult(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "validation_results"

    screening_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screenings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    declaration_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("declarations.id", ondelete="SET NULL"), nullable=True
    )
    rule_version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rule_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    result: Mapped[ScreeningResult] = mapped_column(
        Enum(ScreeningResult, name="validation_result_state"), nullable=False, index=True
    )
    # Deterministic, human-readable explanation of why this result was
    # reached — never an LLM judgment call (docs/ARCHITECTURE.md §3/§10).
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    screening: Mapped["Screening"] = relationship(back_populates="validation_results")
    declaration: Mapped["Declaration | None"] = relationship()
    rule_version: Mapped["RuleVersion"] = relationship(back_populates="validation_results")
    evidence_records: Mapped[list["Evidence"]] = relationship(
        back_populates="validation_result", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ValidationResult id={self.id} result={self.result.value}>"

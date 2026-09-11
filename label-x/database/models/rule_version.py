"""rule_versions — version-dated effective status + enforced text of a rule.

Per docs/ARCHITECTURE.md §7, a rule is not a single static fact: the same
`regulatory_rules` row can have multiple `rule_versions` rows over time (e.g.
the original 2011 text, then a version reflecting a GSR withdrawal/amendment
effective on a later date). The deterministic rule engine (a later phase)
must resolve which version applies "as of" a given date before evaluating
any declaration against it — never assume the original text is unmodified.

`embedding` is the pgvector-compatible field requested for Phase 2: it holds
the embedding of `enforced_text` once the RAG phase picks an embedding model
and backfills it. It is nullable and unused by this phase.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin
from database.config import get_database_settings
from database.enums import RuleVersionStatus
from database.types import embedding_column

if TYPE_CHECKING:
    from database.models.regulatory_rule import RegulatoryRule
    from database.models.validation_result import ValidationResult


class RuleVersion(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "rule_versions"
    __table_args__ = (
        UniqueConstraint(
            "regulatory_rule_id", "version_number", name="uq_rule_versions_rule_version_number"
        ),
        Index("ix_rule_versions_effective_range", "effective_from", "effective_to"),
        Index("ix_rule_versions_status", "status"),
    )

    regulatory_rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("regulatory_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[RuleVersionStatus] = mapped_column(
        Enum(RuleVersionStatus, name="rule_version_status"), nullable=False
    )
    # e.g. "GSR 748(E) dated 24.10.2011" — nullable, only set when a version
    # change was caused by a specific notification.
    citation: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # The exact text or paraphrase actually enforced by the deterministic
    # engine for this version (docs/ARCHITECTURE.md §7) — not the full PDF
    # text, and never edited by AI.
    enforced_text: Mapped[str] = mapped_column(Text, nullable=False)

    # pgvector-prepared embedding of `enforced_text` (see module docstring).
    embedding: Mapped[list[float] | None] = mapped_column(
        embedding_column(get_database_settings().embedding_dim), nullable=True
    )

    regulatory_rule: Mapped["RegulatoryRule"] = relationship(back_populates="versions")
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        back_populates="rule_version"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<RuleVersion regulatory_rule_id={self.regulatory_rule_id} "
            f"version_number={self.version_number} status={self.status.value}>"
        )

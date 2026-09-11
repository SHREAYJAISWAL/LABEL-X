"""regulatory_rules — canonical identity of a rule/provision.

A row here identifies *which* provision (e.g. "Rule 6, sub-rule (1)(c)") —
not its current wording or effective status, which are version-dated facts
that live in `rule_versions` (docs/ARCHITECTURE.md §7). No rule content is
seeded by this phase; see `database/seed.py`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from database.models.rule_version import RuleVersion


class RegulatoryRule(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "regulatory_rules"
    __table_args__ = (
        UniqueConstraint("rule_number", "sub_rule", name="uq_regulatory_rules_rule_subrule"),
    )

    # e.g. "6" — the top-level rule number within the source instrument.
    rule_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # e.g. "1(a)" — sub-rule/clause reference, nullable when the rule has none.
    sub_rule: Mapped[str | None] = mapped_column(String(50), nullable=True)

    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # e.g. "Second Schedule" — nullable, only set when the rule depends on one.
    schedule_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_document: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="Legal Metrology (Packaged Commodities) Rules, 2011",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    versions: Mapped[list["RuleVersion"]] = relationship(
        back_populates="regulatory_rule", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RegulatoryRule rule_number={self.rule_number!r} sub_rule={self.sub_rule!r}>"

"""declarations — the extracted-field envelope for one screening.

Mirrors docs/ARCHITECTURE.md §6 exactly: the declaration record has one slot
per legally-relevant field, and every individual field is stored as a JSONB
"envelope" object rather than a bare value, so the shape below is preserved
for every field without needing a separate table per field:

    {
        "value": <any>,
        "present": <bool>,
        "confidence": <float>,
        "evidence_bbox": <[x, y, w, h] | null>,
        "source_image_or_panel": <str | null>,
        "ocr_text": <str | null>
    }

No AI/OCR wiring happens in this phase — the column exists so later phases
have somewhere typed to write extraction output, and so the rule engine has
a stable, versioned shape to read from regardless of which extraction phase
populated it.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from database.models.screening import Screening

# Type alias only, for readability — the actual column type is JSONB either way.
FieldEnvelope = dict


class Declaration(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "declarations"

    screening_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screenings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Each of these is a nullable JSONB field-envelope — see module docstring.
    commodity_name: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    manufacturer: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    packer: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    importer: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    net_quantity_value: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    net_quantity_unit: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    mrp: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    manufacture_date: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    packing_date: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    import_date: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    consumer_complaint_contact: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)
    dimensions: Mapped[FieldEnvelope | None] = mapped_column(JSONB, nullable=True)

    # Open-ended: a JSONB list of field-envelope objects, each additionally
    # carrying its own "label", for provisions not yet modeled as first-class
    # columns above (docs/ARCHITECTURE.md §6).
    other_declarations: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    screening: Mapped["Screening"] = relationship(back_populates="declarations")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Declaration id={self.id} screening_id={self.screening_id}>"

"""evidence — binds a validation result to its source image region / OCR span.

Implements the evidence-first traceability requirement in
docs/ARCHITECTURE.md §5: "No finding without a linked bounding box, OCR
source, rule id/version, and the extracted field(s) it was evaluated
against." `validation_result_id` supplies the rule id/version link;
`image_id` + `bbox` supply the region; `ocr_result_id` supplies the OCR span.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from database.models.image import Image
    from database.models.ocr_result import OCRResult
    from database.models.validation_result import ValidationResult


class Evidence(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "evidence"

    validation_result_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("validation_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("images.id", ondelete="SET NULL"), nullable=True
    )
    ocr_result_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ocr_results.id", ondelete="SET NULL"), nullable=True
    )

    # e.g. {"x": 10, "y": 20, "w": 100, "h": 30} — pixel-space on `image_id`.
    bbox: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    validation_result: Mapped["ValidationResult"] = relationship(
        back_populates="evidence_records"
    )
    image: Mapped["Image | None"] = relationship(back_populates="evidence_records")
    ocr_result: Mapped["OCRResult | None"] = relationship(back_populates="evidence_records")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Evidence id={self.id} validation_result_id={self.validation_result_id}>"

"""ocr_results — raw OCR output for one image.

`tokens` holds the per-token text/bbox/confidence list described in
docs/ARCHITECTURE.md §5-6 as JSONB, e.g.:
`[{"text": "500", "bbox": [x, y, w, h], "confidence": 0.97}, ...]`.
This phase defines the table only — no OCR engine (PaddleOCR) is wired in.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from database.models.evidence import Evidence
    from database.models.image import Image


class OCRResult(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "ocr_results"

    image_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    engine: Mapped[str] = mapped_column(String(50), nullable=False, default="paddleocr")
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    image: Mapped["Image"] = relationship(back_populates="ocr_results")
    evidence_records: Mapped[list["Evidence"]] = relationship(back_populates="ocr_result")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OCRResult id={self.id} image_id={self.image_id} engine={self.engine!r}>"

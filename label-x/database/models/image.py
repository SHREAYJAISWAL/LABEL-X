"""images — uploaded package photos belonging to a screening.

`storage_path` is a location reference (local path or object-store key/URL)
rather than the image bytes themselves — this phase does not implement
upload handling or storage, only the table it will write to.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from database.models.evidence import Evidence
    from database.models.ocr_result import OCRResult
    from database.models.screening import Screening


class Image(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "images"

    screening_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screenings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Set once panel detection (docs/ARCHITECTURE.md §5) runs; null until then.
    is_principal_display_panel: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    screening: Mapped["Screening"] = relationship(back_populates="images")
    ocr_results: Mapped[list["OCRResult"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )
    evidence_records: Mapped[list["Evidence"]] = relationship(back_populates="image")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Image id={self.id} screening_id={self.screening_id}>"

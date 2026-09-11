"""users — inspectors/admins who operate LABEL-X.

Authentication itself is out of scope for this phase (see
docs/PROJECT_STATUS.md); `hashed_password` is nullable so the table can be
populated (e.g. by a seed script) before an auth phase decides on a hashing
scheme.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPKMixin
from database.enums import UserRole

if TYPE_CHECKING:
    from database.models.audit_log import AuditLog
    from database.models.screening import Screening


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.INSPECTOR
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    screenings: Mapped[list["Screening"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<User id={self.id} email={self.email!r} role={self.role.value}>"

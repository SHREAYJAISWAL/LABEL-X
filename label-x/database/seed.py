"""Seed structure for local/demo use.

Deliberately minimal for this phase: only a demo inspector account. Per
docs/ARCHITECTURE.md design principle #11 ("no invented legal requirements"),
this script does not fabricate `regulatory_rules` / `rule_versions` content —
that data must come from the actual source PDF, which is the job of the
phase that builds `rules/`, not this one.

All seed functions are idempotent (safe to run repeatedly): each looks up
its row before inserting, rather than assuming an empty table.

Run directly:
    python -m database.seed
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from database.enums import UserRole
from database.models.user import User
from database.session import session_scope

logger = logging.getLogger(__name__)

DEMO_INSPECTOR_EMAIL = "inspector@labelx.local"


def seed_demo_user(db: Session) -> User:
    """Ensure a single demo inspector user exists; return it either way.

    `hashed_password` is left unset (None) — this phase does not implement
    authentication, so there is no hashing scheme to apply yet.
    """

    existing = db.query(User).filter(User.email == DEMO_INSPECTOR_EMAIL).one_or_none()
    if existing is not None:
        logger.info("Demo inspector already exists: %s", existing.email)
        return existing

    user = User(
        email=DEMO_INSPECTOR_EMAIL,
        full_name="Demo Inspector",
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db.add(user)
    db.flush()  # populate user.id without committing yet
    logger.info("Created demo inspector: %s", user.email)
    return user


def seed_all() -> None:
    with session_scope() as db:
        seed_demo_user(db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | %(message)s")
    seed_all()
    print("Seed complete.")

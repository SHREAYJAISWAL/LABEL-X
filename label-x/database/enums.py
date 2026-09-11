"""Enumerations shared across database models.

`ScreeningResult` mirrors the three-state result model from
docs/ARCHITECTURE.md §3 exactly — no other output shape is permitted for a
screening or a per-rule validation result.
"""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    INSPECTOR = "inspector"
    ADMIN = "admin"
    VIEWER = "viewer"


class ScreeningStatus(str, enum.Enum):
    """Pipeline lifecycle status of a screening — not the compliance result."""

    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScreeningResult(str, enum.Enum):
    """The only three permitted outcomes for a screening or a validation
    result (docs/ARCHITECTURE.md §3). Never a numeric compliance score."""

    NO_OBVIOUS_ISSUE = "no_obvious_issue"
    NEEDS_REVIEW = "needs_review"
    POTENTIAL_NON_COMPLIANCE = "potential_non_compliance"


class RuleVersionStatus(str, enum.Enum):
    """Effective status of a specific rule version (docs/ARCHITECTURE.md §7)."""

    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    AMENDED = "amended"
    SUPERSEDED = "superseded"

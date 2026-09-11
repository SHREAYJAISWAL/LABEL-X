"""All LABEL-X ORM models.

Importing this package registers every model on `database.base.Base`, which
is what `Base.metadata` (used by `create_all()` and by Alembic autogenerate)
needs to see the full schema. Always import models via this package rather
than importing individual model modules directly, to avoid registration-order
surprises.
"""

from database.models.audit_log import AuditLog
from database.models.declaration import Declaration
from database.models.evidence import Evidence
from database.models.image import Image
from database.models.ocr_result import OCRResult
from database.models.regulatory_rule import RegulatoryRule
from database.models.rule_version import RuleVersion
from database.models.screening import Screening
from database.models.user import User
from database.models.validation_result import ValidationResult

__all__ = [
    "AuditLog",
    "Declaration",
    "Evidence",
    "Image",
    "OCRResult",
    "RegulatoryRule",
    "RuleVersion",
    "Screening",
    "User",
    "ValidationResult",
]

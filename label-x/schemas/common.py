"""Framework-agnostic schemas shared across backend, frontend, and tests.

Phase 1 scope only: liveness + error envelope. Domain schemas (declarations,
extracted fields, results) belong in their own modules once that phase is
built — see docs/PROJECT_STATUS.md.
"""

from __future__ import annotations

from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int

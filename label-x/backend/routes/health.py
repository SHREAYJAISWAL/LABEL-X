"""Liveness endpoint.

Phase 1: reports process liveness only. Once the database and any external
AI service are introduced, this should be extended to report their
reachability too, so `/health` never reports "ok" while a real dependency is
down (see docs/PROJECT_STATUS.md, "Known issues").
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.config import get_settings
from schemas.common import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus, summary="Liveness check")
def health() -> HealthStatus:
    settings = get_settings()
    return HealthStatus(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )

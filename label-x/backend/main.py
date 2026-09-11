"""LABEL-X FastAPI application entrypoint.

Phase 1 scope: application scaffolding only — health endpoint, config,
logging, and consistent error handling. No OCR, AI, RAG, or rule-validation
routes yet (see docs/PROJECT_STATUS.md for what's implemented).

Run locally with:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# Registering the handler against Starlette's base HTTPException (rather than
# fastapi.HTTPException, which subclasses it) is what makes this also catch
# exceptions Starlette's own routing raises internally, e.g. 404s for
# unmatched routes.
from starlette.exceptions import HTTPException as HTTPException

from backend.config import get_settings
from backend.logging_config import configure_logging, get_logger
from backend.routes.health import router as health_router
from schemas.common import ErrorResponse

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "LABEL-X — inspection-assistance and preliminary screening system for "
            "Legal Metrology (Packaged Commodities) Rules, 2011 compliance. "
            "This API never issues a final legal determination; see /health for "
            "liveness and docs/ARCHITECTURE.md for the full pipeline."
        ),
    )

    origins = (
        ["*"]
        if settings.cors_allow_origins == "*"
        else [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)

    @app.get("/", tags=["root"], summary="Service info")
    def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "docs": "/docs",
            "health": "/health",
        }

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning("HTTP %s on %s: %s", exc.status_code, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="http_error",
                detail=str(exc.detail),
                status_code=exc.status_code,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internals (stack traces, exception args) to the client.
        # Full detail goes to the log only.
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                detail="An unexpected error occurred. This has been logged.",
                status_code=500,
            ).model_dump(),
        )

    logger.info(
        "LABEL-X backend initialized (env=%s, version=%s)",
        settings.app_env,
        settings.app_version,
    )
    return app


app = create_app()

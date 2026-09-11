"""Basic console logging setup for the LABEL-X backend.

Phase 1 scope: a single, consistent console format across the app. No
structured/JSON logging or log shipping yet — deferred until it's actually
needed by a later phase.
"""

from __future__ import annotations

import logging

_CONFIGURED = False


def configure_logging(log_level: str = "INFO") -> None:
    """Idempotently configure root logging for the process."""

    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

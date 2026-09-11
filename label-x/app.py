"""LABEL-X Streamlit dashboard.

Phase 1 scope: a dashboard shell that confirms the backend is reachable and
lays out where each later phase's UI will go. No image upload, OCR, AI
extraction, RAG, or rule validation UI yet — those are added phase by phase
per docs/PROJECT_STATUS.md.

Run locally with:
    streamlit run frontend/app.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure the repo root is importable regardless of the working directory
# `streamlit run` is invoked from — it only puts this file's own directory
# on sys.path by default, which would break the `frontend.config` import.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
import streamlit as st

from frontend.config import get_frontend_settings

settings = get_frontend_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="LABEL-X", page_icon="🏷️", layout="wide")


def fetch_backend_health() -> dict | None:
    """Call the backend /health endpoint. Returns None (never raises) on failure."""

    try:
        response = requests.get(f"{settings.backend_url}/health", timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        # The app must never crash if the backend is unavailable — this is the
        # frontend half of the "external service failure must not crash the
        # app" requirement in docs/ARCHITECTURE.md.
        logger.warning("Backend health check failed: %s", exc)
        return None


def render_header() -> None:
    st.title("🏷️ LABEL-X")
    st.caption(
        "AI-assisted preliminary screening for Legal Metrology "
        "(Packaged Commodities) Rules, 2011 compliance — "
        "**inspection assistance, not a legal certification.**"
    )


def render_backend_status() -> None:
    st.subheader("System status")
    health = fetch_backend_health()

    if health is None:
        st.error(
            f"Backend unreachable at `{settings.backend_url}`. "
            "Start it with `uvicorn backend.main:app --reload` and refresh this page."
        )
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Backend", health.get("status", "unknown").upper())
    col2.metric("Environment", health.get("environment", "unknown"))
    col3.metric("Version", health.get("version", "unknown"))
    st.success(f"Connected to {health.get('app_name', 'backend')}.")


def render_pipeline_placeholder() -> None:
    st.subheader("Screening pipeline")
    st.info(
        "Upload, OCR, AI field extraction, regulatory retrieval, and rule "
        "validation are not implemented yet — this dashboard is the Phase 1 "
        "foundation only. See `docs/PROJECT_STATUS.md` for the current phase "
        "and `docs/ARCHITECTURE.md` for the full planned pipeline."
    )

    stages = [
        "1. Upload package image",
        "2. Image quality check",
        "3. OCR (PaddleOCR)",
        "4. Multimodal field extraction",
        "5. Category & applicability determination",
        "6. Regulatory retrieval (RAG)",
        "7. Deterministic rule validation",
        "8. Three-state result + evidence",
        "9. Inspector review / override",
        "10. Report generation",
    ]
    st.write("\n".join(f"- {s}" for s in stages))


def render_sidebar() -> None:
    with st.sidebar:
        st.header("LABEL-X")
        st.caption("Team AI Alchemist · SIH 2026 · PS ID 26034")
        st.divider()
        st.caption(f"Backend URL: `{settings.backend_url}`")
        st.caption(f"Environment: `{settings.app_env}`")
        if st.button("Re-check backend"):
            st.rerun()


def main() -> None:
    render_sidebar()
    render_header()
    render_backend_status()
    st.divider()
    render_pipeline_placeholder()


# Streamlit executes this script top-to-bottom on every run/rerun (via
# `streamlit run`, where it's loaded as __main__), so main() is simply
# called at module level rather than gated behind an __main__ check.
main()

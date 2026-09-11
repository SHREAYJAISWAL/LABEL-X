"""LABEL-X database layer.

SQLAlchemy models, session/engine management, and Alembic migration glue for
PostgreSQL. This package does not implement OCR, AI extraction, or RAG — it
only defines and manages the schema described in
`docs/ARCHITECTURE.md` §8 and provisioned by `docs/PROJECT_STATUS.md` Phase 2.
"""

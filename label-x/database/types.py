"""Custom SQLAlchemy column types shared across models.

`embedding_column()` provides the pgvector-compatible field required for
regulatory rule embeddings ahead of the RAG phase (docs/ARCHITECTURE.md §7-8).
It uses the real `pgvector.sqlalchemy.Vector` type when the optional
`pgvector` package (and, at the database level, the `vector` extension) is
available, and degrades to a plain JSON column otherwise so the rest of the
app — and the schema-level tests — keep working in environments where the
pgvector package/extension hasn't been installed yet. No embeddings are
computed or written by this phase; the column exists purely so the RAG phase
does not need a schema migration later.
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.types import TypeEngine

try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when pgvector isn't installed
    PGVECTOR_AVAILABLE = False


def embedding_column(dim: int) -> TypeEngine:
    """Return the column type for a `dim`-dimensional embedding vector.

    Real `VECTOR(dim)` (requires the pgvector Python package and the
    Postgres `vector` extension — see `database/init_db.py`) when available,
    otherwise a JSON fallback holding a plain list of floats.
    """

    if PGVECTOR_AVAILABLE:
        return Vector(dim)
    return JSON()

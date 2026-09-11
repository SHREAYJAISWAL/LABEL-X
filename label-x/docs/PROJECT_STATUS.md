# LABEL-X — Project Status

Read this file first at the start of every new phase. Continue from what exists;
do not rebuild anything already done.

## Completed phases

### Phase 0 — Repository bootstrap & planning (done)
- Inspected repository: no prior code existed.
- Read both source documents in full:
  - `9_The_Legal_Metrology__Package_Commodities__Rules__2011.pdf` (43 pages, Rules
    1–34 + Schedules I–VII, including amendment/withdrawal annotations).
  - `SMART_INDIA_HACKATHON_2026.pptx` (7 slides: problem statement, gap analysis,
    proposed solution, tech stack, scalability, limitations/future scope).
- Created initial directory structure and planning docs (this phase produces no
  application code).

### Phase 1 — Project foundation (done)
- Inspected repository and read `docs/PROJECT_STATUS.md`, `docs/ARCHITECTURE.md`,
  `docs/RULE_IMPLEMENTATION_PLAN.md` before starting; nothing pre-existing was
  rebuilt.
- Built the FastAPI backend skeleton: config (`pydantic-settings`, env-var driven),
  logging, `/health` endpoint, root `/` service-info endpoint, and consistent
  JSON error handling for both explicit `HTTPException`s and unhandled exceptions
  (including Starlette's internal 404 for unmatched routes).
- Built the Streamlit frontend skeleton: dashboard shell that checks backend
  connectivity via `/health`, never crashes if the backend is unreachable, and
  lays out placeholders for every later pipeline stage.
- Added shared, framework-agnostic Pydantic schemas (`schemas/common.py`):
  `HealthStatus`, `ErrorResponse` — used by both backend and tests.
- Replaced the empty `.env.example`, `requirements.txt`, `README.md`
  placeholders from Phase 0 with real content.
- Added `deployment/Dockerfile.backend`, `deployment/Dockerfile.frontend`,
  `deployment/docker-compose.yml` — backend + frontend only, no database or AI
  service containers yet, no k8s/Kafka.
- Added `tests/test_health.py` (4 tests): health endpoint, root endpoint, 404
  error envelope, shared-schema import sanity check.
- **Verified live, not just imported:** ran `uvicorn` and hit
  `GET /health` and `GET /` over real HTTP (200 with expected JSON), hit an
  unmatched route (404 with the standard error envelope), and ran
  `streamlit run frontend/app.py` headless and confirmed it serves HTTP 200.
  Confirmed no hardcoded secrets via grep across `backend/`, `frontend/`,
  `schemas/`, `tests/`.
- One bug found and fixed during verification: the exception handler was
  registered against `fastapi.HTTPException`, which didn't catch the
  `starlette.exceptions.HTTPException` that Starlette's router raises
  internally for unmatched routes (404s went out as FastAPI's default body
  instead of the project's `ErrorResponse` envelope). Fixed by registering the
  handler against Starlette's base `HTTPException` class instead.

### Phase 2 — Database layer (done, with one important caveat — see below)

- Inspected the repository and this file before starting. **Note:** the
  repository handed off for this phase was a flattened text export that only
  actually contained six root-level files (`README.md`, `ARCHITECTURE.md`,
  `PROJECT_STATUS.md`, `RULE_IMPLEMENTATION_PLAN.md`, `app.py`, `main.py`) —
  `backend/`, `frontend/`, and `schemas/` were referenced by imports but not
  present in the export. Those modules were reconstructed from the behavior
  documented in Phase 1's own notes above (config/logging/health-route
  shapes, the Streamlit dashboard shell, `HealthStatus`/`ErrorResponse`)
  before Phase 2 work began, so the app has an internally consistent base to
  build on. If your real repository's `backend/`/`frontend/`/`schemas/`
  differ from this reconstruction, replace them with your originals — Phase
  2's database layer does not depend on their internals, only on `schemas`
  existing as an importable package.
- Built the full SQLAlchemy (2.0-style) database layer under `database/`:
  - `database/config.py` — `DatabaseSettings` (pydantic-settings), reads
    `DATABASE_URL` or assembles one from `POSTGRES_*` env vars. No
    credentials hardcoded anywhere.
  - `database/base.py` — `Base` (declarative base), `UUIDPKMixin` (UUID
    primary key, client-generated via `uuid4()`), `TimestampMixin`
    (`created_at`/`updated_at`, DB-maintained).
  - `database/enums.py` — `UserRole`, `ScreeningStatus`, `ScreeningResult`
    (the three-state model from `docs/ARCHITECTURE.md` §3 — no other output
    shape is permitted), `RuleVersionStatus`.
  - `database/types.py` — `embedding_column(dim)`: pgvector-compatible
    column type for regulatory-rule embeddings (`docs/ARCHITECTURE.md` §7-8),
    using the real `pgvector.sqlalchemy.Vector` type when the optional
    `pgvector` package is installed, degrading to a plain JSON column of
    floats otherwise so the schema still works before pgvector is fully
    provisioned. No embeddings are computed by this phase.
  - `database/models/` — all 10 tables from `docs/ARCHITECTURE.md` §8:
    `users`, `screenings`, `images`, `ocr_results`, `declarations`,
    `regulatory_rules`, `rule_versions` (carries the embedding column),
    `validation_results`, `evidence`, `audit_logs`. UUID PKs, FKs (with
    considered `ondelete` behavior per relationship), indexes on every FK
    plus a few composite indexes for common access patterns
    (`screenings(status, created_at)`, `rule_versions(effective_from,
    effective_to)`, `audit_logs(screening_id, created_at)`,
    `audit_logs(user_id, created_at)`), JSONB for structured/open-ended
    data. `declarations` mirrors the field-envelope shape from
    `docs/ARCHITECTURE.md` §6 exactly (`value`/`present`/`confidence`/
    `evidence_bbox`/`source_image_or_panel`/`ocr_text` per field, as JSONB).
    `regulatory_rules`/`rule_versions` are split per §7 (rule identity vs.
    version-dated effective status/text) with a unique constraint on
    `(regulatory_rule_id, version_number)`.
  - `database/session.py` — engine (`pool_pre_ping` on by default),
    `SessionLocal`, `get_db()` (FastAPI-style dependency), `session_scope()`
    (context manager for scripts).
  - `database/init_db.py` — `check_connection()` (never raises, returns
    bool — safe for a future `/health` extension), `enable_pgvector_extension()`
    (best-effort `CREATE EXTENSION IF NOT EXISTS vector`), `init_db()`
    (`Base.metadata.create_all()` for local/demo use — Alembic remains the
    source of truth otherwise). Runnable directly: `python -m database.init_db`.
  - `database/seed.py` — idempotent seed structure. Deliberately seeds only
    a demo inspector user for now; does **not** fabricate
    `regulatory_rules`/`rule_versions` content, per design principle #11
    (no invented legal requirements) — that data must come from the actual
    source PDF in the phase that builds `rules/`. Runnable directly:
    `python -m database.seed`.
  - `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`,
    `alembic/versions/0001_initial_schema.py` — Alembic wired to
    `database.config`'s settings (one place owns the connection string) and
    to `Base.metadata`. The initial revision is hand-written to mirror the
    models exactly (see caveat below on why, and verify it before relying
    on it — details in "Known issues").
- Updated `deployment/docker-compose.yml` to add a `db` service
  (`pgvector/pgvector:pg16` image, so the extension is available without a
  separate install step) with a healthcheck, and wired `backend`'s
  `DATABASE_URL` to it via `depends_on: condition: service_healthy`.
- Updated `.env.example`, `requirements.txt` (added SQLAlchemy, Alembic,
  psycopg2-binary, pgvector, python-dotenv, httpx for the test client).
- Added `tests/test_database.py`: schema-level tests that need no live
  database connection (all expected tables/columns/FKs/constraints
  registered on `Base.metadata`, mapper configuration is consistent,
  embedding column present on `rule_versions`, declaration field-envelope
  columns present) plus live-database integration tests that insert/read a
  full chain of rows across all 10 tables — these auto-skip (not fail) if
  `TEST_DATABASE_URL` isn't set or the database isn't reachable.

**⚠ Not verified by actually running: no live test run yet.** The sandbox
this phase was built in has no network access and none of the required
packages (SQLAlchemy, FastAPI, pydantic, pytest, psycopg2, alembic, pgvector)
were installable. Every file was written carefully and cross-checked by hand
(enum value lists compared between `database/enums.py` and the migration
line-by-line, every `relationship(back_populates=...)` pair checked for a
matching reverse declaration, every forward-referenced type string checked
against its `TYPE_CHECKING` import, all Python files pass `py_compile`), but
none of this has been exercised by an actual interpreter with SQLAlchemy
loaded, an actual `pytest` run, or an actual PostgreSQL connection. **Before
trusting this phase, run the verification commands below in a normal
environment and fix anything they surface** — treat this phase as
code-complete-but-unverified rather than done-and-checked, which the previous
phases in this document were able to be.

## Current phase

**Phase 2 — Database layer. Code-complete, unverified — see caveat above.**
OCR, AI extraction, RAG, rule validation logic, and authentication remain
explicitly out of scope and are not implemented; only the tables they'll
eventually read/write now exist.

## Files created

```
label-x/
├── .env.example                        (real template, no secrets)
├── README.md                           (setup/run/test instructions)
├── requirements.txt                    (backend + frontend deps only)
├── docs/PROJECT_STATUS.md              (this file, updated)
├── backend/
│   ├── __init__.py
│   ├── main.py                         (FastAPI app, CORS, error handlers)
│   ├── config.py                       (pydantic-settings, env-var driven)
│   ├── logging_config.py               (basic console logging)
│   └── routes/
│       ├── __init__.py
│       └── health.py                   (GET /health)
├── frontend/
│   ├── __init__.py
│   ├── app.py                          (Streamlit dashboard shell)
│   └── config.py                       (env-var driven frontend settings)
├── schemas/
│   ├── __init__.py
│   └── common.py                       (HealthStatus, ErrorResponse)
├── tests/
│   ├── __init__.py
│   └── test_health.py                  (4 tests, all passing)
└── deployment/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── docker-compose.yml
```

`vision/`, `ocr/`, `rules/`, `rag/`, `services/`, `data/` remain empty
(`.gitkeep` only) — untouched, per phase scope. `database/` is populated as
of Phase 2 (see below).

```
label-x/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
└── database/
    ├── __init__.py
    ├── config.py
    ├── base.py
    ├── enums.py
    ├── types.py
    ├── session.py
    ├── init_db.py
    ├── seed.py
    └── models/
        ├── __init__.py
        ├── user.py
        ├── screening.py
        ├── image.py
        ├── ocr_result.py
        ├── declaration.py
        ├── regulatory_rule.py
        ├── rule_version.py
        ├── validation_result.py
        ├── evidence.py
        └── audit_log.py
```

## Files modified

- Phase 1: `.env.example`, `requirements.txt`, `README.md` — filled in from
  Phase 0's empty placeholders.
- Phase 2: `.env.example` (added `DATABASE_URL`/`POSTGRES_*`/`EMBEDDING_DIM`/
  `DB_AUTO_CREATE`), `requirements.txt` (added database deps),
  `deployment/docker-compose.yml` (added the `db` service and backend
  `DATABASE_URL` wiring), `deployment/Dockerfile.backend` (copies
  `database/`, `alembic/`, `alembic.ini`).

## Tests completed

Phase 1 (previously verified live, see notes above):
```
tests/test_health.py::test_health_returns_ok                              PASSED
tests/test_health.py::test_root_returns_service_info                      PASSED
tests/test_health.py::test_unknown_route_returns_standard_error_envelope  PASSED
tests/test_health.py::test_shared_schemas_are_importable                  PASSED
```

Phase 2 (written, NOT yet run — see caveat above):
```
tests/test_database.py::test_all_expected_tables_are_registered
tests/test_database.py::test_mapper_configuration_is_consistent
tests/test_database.py::test_every_table_has_uuid_pk_and_timestamps[...]   (x10)
tests/test_database.py::test_foreign_keys_point_at_expected_tables
tests/test_database.py::test_regulatory_rule_uniqueness_constraint_present
tests/test_database.py::test_rule_version_uniqueness_constraint_present
tests/test_database.py::test_rule_version_has_embedding_column
tests/test_database.py::test_declaration_field_envelope_columns_present
tests/test_database.py::test_live_can_insert_and_read_back_a_full_chain    (skips without TEST_DATABASE_URL)
tests/test_database.py::test_live_ocr_result_and_declaration_json_roundtrip (skips without TEST_DATABASE_URL)
```

## Known issues / open questions for you

1. The Rule Implementation Plan flags several provisions whose **current effective
   status depends on GSR 748(E) dated 24.10.2011 (effective 01.07.2012)** and GSR
   734(E) dated 30.09.2011. Recorded as withdrawn/amended per the PDF's own
   annotations — still worth confirming nothing's changed since 2011 before Phase
   4/5 hard-codes them as "currently active".
2. No decision yet on which multimodal vision model / API to use for field
   extraction, or which embedding model for pgvector — deferred to the phase that
   implements `vision/` and `rag/`.
3. No decision yet on how "measured net quantity" (needed for Rule 22 MPE checks)
   gets into the system for an image-only demo — likely a manual inspector-entered
   field for the quantity-focused phase, not something OCR can determine on its
   own. Flagged in the Rule Implementation Plan.
4. CORS is wide open (`*`) by default for local/demo convenience — fine for the
   SIH prototype, should be tightened if this is ever deployed beyond a demo.
5. `/health` currently only reports process liveness, not dependency health —
   correct for Phase 1 (no dependencies exist yet), but should be extended once
   the database/AI service are introduced so it doesn't give a false "ok".

## Important architectural decisions

- Pydantic validates AI *output structure*, never legal compliance.
- The rule engine is the only component permitted to emit a finding; RAG only
  retrieves candidate rule text, it never decides.
- Regulatory rules are versioned data (rule number + effective dates +
  withdrawn/amended status + citation), not hardcoded conditionals — this is
  required by the source PDF containing multiple amendment/withdrawal notes.
- Three-state result model (`NO OBVIOUS ISSUE` / `NEEDS REVIEW` /
  `POTENTIAL NON-COMPLIANCE`) is the only allowed output shape for a screening;
  no numeric "compliance score" is ever generated.
- Demo categories are Biscuits, Tea, Soap, Cereals/Pulses, Salt — chosen because
  four of the five appear directly in the Second Schedule (standard pack sizes),
  giving a natural, legally-grounded demo path.
- Build order for rule engine: applicability/exemption gatekeepers (Rules 3, 26)
  → core declarations (Rule 6, 9, 10) → standard sizes (Rule 5) → units/qualifiers
  (Rules 11, 12, 13) → PDP/lettering (Rules 7, 8, heuristic only) → quantity/MPE
  (Rule 22, 19, 21, narrow scope). See `RULE_IMPLEMENTATION_PLAN.md` §"Build order
  recommendation".

## Known issues / open questions for you (Phase 2)

1. **Run the verification commands below before trusting this phase.** This
   phase could not be executed in the sandbox it was built in (no network,
   none of SQLAlchemy/Alembic/psycopg2/pgvector/pytest installable). It was
   hand-verified as thoroughly as static review allows, but that is not a
   substitute for actually running it once.
2. The hand-written Alembic migration (`0001_initial_schema.py`) was
   authored to mirror the models column-for-column since `alembic revision
   --autogenerate` couldn't be run here either. Once you have a real
   database available, run `alembic upgrade head` against an empty database,
   then `alembic revision --autogenerate -m "check"` — it should generate an
   **empty** migration (no diff) if the hand-written one matches the models.
   If it doesn't come back empty, trust the autogenerate diff over the
   hand-written file and fix the migration.
3. `backend/`, `frontend/`, and `schemas/` in this delivery are Phase 2's
   reconstruction of what Phase 1's notes describe, not necessarily
   byte-identical to your actual prior code (see the Phase 2 section above
   for why). If you have the real versions, swap them back in — the database
   layer only imports `schemas` as a package and doesn't touch
   `backend`/`frontend` internals.
4. `embedding_dim` (`.env`'s `EMBEDDING_DIM`, default 1536) is a placeholder
   until the RAG phase picks an actual embedding model — changing it later
   requires a new migration (`ALTER COLUMN ... TYPE vector(N)`), so picking
   the real model before generating much rule data will save a migration.
5. `validation_results.rule_version_id` uses `ondelete="RESTRICT"` (a rule
   version that has already been used in a finding can't be deleted out from
   under it) while most other FKs use `SET NULL` or `CASCADE` — worth
   confirming this matches how you want historical findings to behave if a
   rule version is later corrected.
6. Previously open items from Phase 1 (rule effective-status confirmation,
   vision/embedding model choice, how measured net quantity enters the
   system, CORS, `/health` dependency reporting) are unchanged and still
   apply — see Phase 1 notes above.

## Important architectural decisions (Phase 2 additions)

- `regulatory_rules` (rule identity) and `rule_versions` (version-dated
  effective status + enforced text + embedding) are two tables, not one —
  required by `docs/ARCHITECTURE.md` §7 treating a rule as a version-dated
  fact, not a static one.
- The pgvector embedding column lives on `rule_versions`, not
  `regulatory_rules` — RAG retrieval should match against the text that's
  actually enforced for a given version, not a rule-level summary.
- `declarations` uses one JSONB "field-envelope" column per legally-relevant
  field (matching `docs/ARCHITECTURE.md` §6's per-field shape) rather than a
  separate table per field or per extraction attempt — keeps the rule engine
  and reviewer UI reading from one row per screening, while still retaining
  every field's own confidence/bbox/OCR-source independently.
- `screenings.status` (pipeline lifecycle) and `screenings.overall_result`
  (three-state compliance outcome) are separate columns — conflating them
  would make "still processing" indistinguishable from "reviewed and found
  compliant."

## Next phase

Awaiting your instruction for **Phase 3**. Natural candidates, in order of the
core pipeline (per `docs/ARCHITECTURE.md` §9 and `RULE_IMPLEMENTATION_PLAN.md`
build order):
- Domain Pydantic schemas (`schemas/`): the declaration model and per-field
  extraction envelope (value/present/confidence/bbox/source/OCR text) from
  `docs/ARCHITECTURE.md` §6, now backed by the `declarations` table — typed
  models plus unit tests, still no OCR/AI wiring.
- OR: image upload + quality check + OpenCV preprocessing skeleton in
  `backend/`/`vision/`, writing to the now-existing `images` table, stubbed
  so the pipeline shape exists before real OCR is wired in.

Tell me which you'd like first, or give different instructions, and I'll inspect
this file plus the repo before starting.

## Verification commands for Phase 1

```bash
cd label-x
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Backend
uvicorn backend.main:app --reload --port 8000 &
curl http://localhost:8000/health

# Frontend (separate terminal)
streamlit run frontend/app.py

# Tests
pytest -v
```

## Verification commands for Phase 2 (run these — see caveat above)

```bash
cd label-x
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set a real POSTGRES_PASSWORD

# Start just Postgres (pgvector-enabled image)
docker compose -f deployment/docker-compose.yml --env-file .env up -d db

# Option A: quick local schema creation (dev/demo)
python -m database.init_db
python -m database.seed

# Option B: Alembic (source of truth otherwise)
alembic upgrade head
# Sanity check the hand-written migration matches the models:
alembic revision --autogenerate -m "check"   # should generate an EMPTY migration

# Tests — schema-level (no live DB needed)
pytest tests/test_database.py -k "not live" -v

# Tests — including live-DB round-trip
export TEST_DATABASE_URL=postgresql+psycopg2://labelx:<password>@localhost:5432/labelx
pytest tests/test_database.py -v

# Full suite
pytest -v
```

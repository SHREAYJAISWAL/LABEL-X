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

## Current phase

**Phase 1 — Project foundation. Complete.** OCR, AI extraction, RAG, rule
validation, and authentication are explicitly out of scope for this phase and
are not implemented.

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

`vision/`, `ocr/`, `rules/`, `rag/`, `database/`, `services/`, `data/` remain
empty (`.gitkeep` only) — untouched, per phase scope.

## Files modified

- `.env.example`, `requirements.txt`, `README.md` — filled in from Phase 0's
  empty placeholders.

## Tests completed

```
tests/test_health.py::test_health_returns_ok                              PASSED
tests/test_health.py::test_root_returns_service_info                      PASSED
tests/test_health.py::test_unknown_route_returns_standard_error_envelope  PASSED
tests/test_health.py::test_shared_schemas_are_importable                  PASSED
```
4 passed, 0 failed. Also manually verified live server behavior (see Phase 1
notes above) beyond what `TestClient`-based tests cover.

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

## Next phase

Awaiting your instruction for **Phase 2**. Natural candidates, in order of the
core pipeline (per `docs/ARCHITECTURE.md` §9 and `RULE_IMPLEMENTATION_PLAN.md`
build order):
- Domain Pydantic schemas (`schemas/`): the declaration model and per-field
  extraction envelope (value/present/confidence/bbox/source/OCR text) from
  `docs/ARCHITECTURE.md` §6 — no OCR/AI wiring yet, just the typed models plus
  unit tests.
- OR: image upload + quality check + OpenCV preprocessing skeleton in
  `backend/`/`vision/`, stubbed so the pipeline shape exists before real OCR is
  wired in.

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

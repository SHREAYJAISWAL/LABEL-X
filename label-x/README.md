# LABEL-X

AI-assisted preliminary screening for compliance of packaged commodities under
the *Legal Metrology (Packaged Commodities) Rules, 2011* — Smart India
Hackathon 2026, Problem Statement ID 26034, Team AI Alchemist.

> LABEL-X is an **inspection-assistance and preliminary screening system**,
> not an automated legal authority. See `docs/ARCHITECTURE.md` for the full
> design and `docs/RULE_IMPLEMENTATION_PLAN.md` for regulatory scope.

## Current status

**Phase 1 — Project foundation.** Backend and frontend scaffolding, config,
logging, error handling, and a `/health` endpoint. No OCR, AI extraction,
RAG, or rule validation yet — see `docs/PROJECT_STATUS.md` for the
up-to-date phase tracker.

## Project structure

```
label-x/
├── backend/        FastAPI app (config, logging, routes)
├── frontend/        Streamlit dashboard
├── schemas/         Shared Pydantic schemas (backend + frontend + tests)
├── database/        SQLAlchemy models, Alembic migrations, PostgreSQL config
├── vision/ ocr/ rules/ rag/ services/   Empty — future phases
├── tests/           Pytest tests
├── deployment/       Dockerfiles + docker-compose.yml
├── docs/            Architecture, rule plan, project status
├── requirements.txt
└── .env.example
```

## Setup (local, without Docker)

Requires Python 3.11+.

```bash
cd label-x
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # edit values if needed; defaults work locally
```

### Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Verify:
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok","app_name":"label-x-backend","version":"0.1.0","environment":"development"}`

Interactive API docs: http://localhost:8000/docs

### Run the frontend

In a second terminal (same virtualenv):

```bash
streamlit run frontend/app.py
```

Open the URL Streamlit prints (default http://localhost:8501). The dashboard
shows live backend connectivity status and a placeholder for each pipeline
stage still to be built.

### Run tests

```bash
pytest
```

## Setup (Docker)

```bash
cd label-x
cp .env.example .env
docker compose -f deployment/docker-compose.yml --env-file .env up --build
```

- Backend: http://localhost:8000/health
- Frontend: http://localhost:8501
- Database: postgres+pgvector on localhost:5432 (see below)

## Database (Phase 2)

PostgreSQL + pgvector, via SQLAlchemy and Alembic. No OCR/AI/RAG logic reads
or writes these tables yet — this phase only provisions the schema described
in `docs/ARCHITECTURE.md` §8.

```bash
cp .env.example .env    # then set a real POSTGRES_PASSWORD

# Start Postgres only (pgvector-enabled image)
docker compose -f deployment/docker-compose.yml --env-file .env up -d db

# Apply migrations
alembic upgrade head

# Or, for quick local/demo use instead of Alembic:
python -m database.init_db

# Optional: seed a demo inspector user
python -m database.seed
```

See `docs/PROJECT_STATUS.md` for the full table list, design decisions, and
verification commands.

## Configuration

All configuration is via environment variables — see `.env.example` for the
full list. Nothing is hardcoded, and no real secrets should ever be
committed.

## Development principles

See `docs/ARCHITECTURE.md` §10 for the full list. In short: work in phases,
inspect `docs/PROJECT_STATUS.md` before starting a new one, keep AI
extraction / RAG retrieval / rule validation in separate modules, never let
an LLM or RAG layer decide compliance, and always fall back to
`NEEDS REVIEW` rather than guessing.

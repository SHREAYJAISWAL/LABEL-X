# LABEL-X — Architecture

Smart India Hackathon 2026 · Problem Statement ID 26034 · Team AI Alchemist (Team ID 3179)

## 1. Purpose

LABEL-X is an **inspection-assistance and preliminary screening system** for checking
packaged-commodity labels against the *Legal Metrology (Packaged Commodities) Rules,
2011*. It is not, and must never present itself as, an automated legal authority. Final
compliance determination always rests with a human Legal Metrology inspector.

## 2. Core principle

```
AI extracts and interprets.
RAG retrieves.
Deterministic rules validate.
Humans decide.
```

Each stage is a separate, independently testable concern:

| Concern | Owner | Never does |
|---|---|---|
| Reading the label (OCR + vision) | `ocr/`, `vision/` | Never decides compliance |
| Structuring what was read | `schemas/` (Pydantic) | Never validates against law |
| Finding the applicable provision | `rag/` | Never issues a final finding |
| Applying the provision | `rules/` (deterministic engine) | Never guesses when evidence is weak |
| Judging the result | Human inspector | — |

## 3. Three-state result model

Every screening resolves to exactly one of:

1. **NO OBVIOUS ISSUE** — declaration(s) detected, legible, and satisfy the applicable
   rule as currently in force.
2. **NEEDS REVIEW** — OCR/vision confidence is low, category or applicability is
   ambiguous, the rule/version status is uncertain, or evidence is otherwise
   insufficient to decide either way.
3. **POTENTIAL NON-COMPLIANCE** — only produced when *all* of the following hold:
   - the rule is applicable to this package/category/context,
   - the rule (or the specific sub-rule/proviso) is confirmed **active** as of the
     relevant date (not withdrawn/superseded),
   - there is sufficient extraction evidence to evaluate the condition,
   - the condition can be evaluated **deterministically** (no LLM judgment call),
   - the evidence positively supports the finding.

If any precondition for state 3 is not met, the system must fall back to
**NEEDS REVIEW**, never silently assume compliance and never silently assume violation.

## 4. Technology stack

| Layer | Technology | Role |
|---|---|---|
| Frontend | Streamlit | Inspector-facing prototype UI: upload, review, evidence viewer, override, report |
| Backend / orchestration | FastAPI (Python) | Coordinates the pipeline as modular services |
| Image processing | OpenCV | Quality checks, preprocessing, panel detection |
| OCR | PaddleOCR | Text + bounding boxes + per-token confidence |
| Vision / semantic understanding | Multimodal vision model | Layout & field understanding (interprets, does not decide) |
| Structured output | Pydantic | Typed schema for every extracted declaration field |
| Regulatory knowledge | PostgreSQL + pgvector | Versioned rule text + embeddings for retrieval |
| Validation | Deterministic Python rule engine | The only component allowed to produce a finding |
| Deployment | Docker / docker-compose | Local/SIH-demo deployment, no k8s/Kafka/microservices |

## 5. Core pipeline

```
Package Image
  → Image Quality Check
  → OpenCV Preprocessing
  → Panel Detection
  → PaddleOCR                      (text, bounding boxes, confidence)
  → Multimodal Field Extraction    (semantic/layout interpretation)
  → Pydantic Validation            (structural validation of AI output only)
  → Product/Package Classification (category, retail vs wholesale, applicability signals)
  → Applicability Engine           (which chapter/rules apply to this package)
  → Regulatory RAG                 (retrieves candidate rule text/version, does NOT decide)
  → Deterministic Rule Engine      (the only component that produces a finding)
  → Evidence Generation            (binds finding to image region + OCR span + rule id)
  → Three-State Result
  → Human Inspector Review / Override
  → Audit Trail / Report
```

### Evidence-first traceability

Every finding must be traceable end-to-end:

```
IMAGE → OCR → EXTRACTED FIELD → APPLICABLE RULE → VALIDATION → FINDING → EVIDENCE
```

No unexplained compliance scores. No finding without a linked bounding box, OCR
source, rule id/version, and the extracted field(s) it was evaluated against.

## 6. Declaration schema (Pydantic)

Every declaration record supports:

- `commodity_name`
- `manufacturer`, `packer`, `importer`
- `net_quantity_value`, `net_quantity_unit`
- `mrp`
- manufacture / packing / import month-year (as applicable to the package type)
- `consumer_complaint_contact`
- `dimensions` (where applicable — e.g. Rule 14/15 style commodities)
- `other_declarations` (open-ended, for provisions not yet modeled as first-class fields)

Every individual extracted field additionally retains:

- `value`
- `present: bool` (present / not present, independent of value confidence)
- `confidence: float`
- `evidence_bbox` (bounding box on the source image/panel)
- `source_image_or_panel`
- `ocr_text` (raw OCR string backing the interpreted value, when applicable)

This lets the rule engine and the human reviewer independently verify *why* a field
was extracted the way it was, without re-running AI.

## 7. Regulatory versioning

The source PDF (*Legal Metrology (Packaged Commodities) Rules, 2011*, notified
7 March 2011, in force from 1 April 2011) contains provisions that were later amended
or withdrawn — notably via **GSR 748(E) dated 24.10.2011** (effective 01.07.2012) and
**GSR 734(E) dated 30.09.2011**. A rule is not a single static fact; it is a
**version-dated fact**. The `rules/` module and the `regulatory_rules` /
`rule_versions` tables must record, for every provision used in validation:

- rule number and sub-rule/clause reference,
- the schedule it depends on (if any),
- effective-from date,
- effective-to date or `withdrawn`/`amended` status with the citation (GSR number,
  date),
- the exact text or paraphrase actually enforced by the deterministic engine.

The rule engine must resolve "which version of this rule applies **today**" (or at a
configurable as-of date) before evaluating any declaration. See
`docs/RULE_IMPLEMENTATION_PLAN.md` for the specific provisions in scope and their
version status as currently understood from the supplied PDF.

## 8. Database (target schema, built incrementally)

`users`, `screenings`, `images`, `ocr_results`, `declarations`, `regulatory_rules`,
`rule_versions`, `validation_results`, `evidence`, `audit_logs`.

Tables are added as the phase that needs them is implemented — not all at once.

## 9. Project structure

```
label-x/
├── backend/       FastAPI app: routes, orchestration of the pipeline stages
├── frontend/       Streamlit app: upload, review, evidence, override, report UI
├── vision/         Multimodal field-extraction client + prompt/schema glue
├── ocr/            PaddleOCR wrapper: text + bounding boxes + confidence
├── schemas/         Pydantic models: declarations, extracted fields, results
├── rules/          Deterministic rule engine + versioned rule definitions (data, not prose)
├── rag/             Regulatory retrieval: embeddings, pgvector queries, candidate rule lookup
├── database/        SQLAlchemy models / migrations for the schema in §8
├── services/         Cross-cutting glue: applicability engine, classification, orchestration helpers
├── data/            Demo/test fixtures (sample label images, expected outputs) — clearly marked as demo data
├── tests/           Unit tests, one set per deterministic rule at minimum
├── docs/            This file, PROJECT_STATUS.md, RULE_IMPLEMENTATION_PLAN.md
├── deployment/       Dockerfiles, docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## 10. Design principles carried through every phase

1. Work in phases; inspect the repo and `docs/PROJECT_STATUS.md` before each one.
2. Never rewrite working code unnecessarily; keep modules small.
3. No Kubernetes, Kafka, microservices, or other infra beyond Docker/docker-compose.
4. Secrets only via environment variables (`.env`, never hardcoded).
5. Pydantic validates AI output; it does not validate legal compliance.
6. Every deterministic rule ships with tests.
7. AI extraction, RAG retrieval, and rule validation stay in separate modules — never
   let the LLM or RAG layer produce or influence the final finding directly.
8. Every important result carries its evidence.
9. External AI service failures are handled gracefully (fallback to demo/cached data
   with a clear on-screen indication) — the app must never crash.
10. When automated determination isn't reliable, the result is NEEDS REVIEW.
11. No fake accuracy statistics, no invented legal requirements, no legal-certification
    claims anywhere in the UI or reports.

## 11. Demo scope

Primary categories: **Biscuits, Tea, Soap, Cereals/Pulses, Salt** — chosen because they
are explicitly listed in the Second Schedule (standard package sizes) and give
coverage across food, non-food, and different unit-of-measure conventions.

Demo must show: upload → quality check → OCR → declaration extraction → evidence
(bounding boxes) → category/context determination → applicable-rule retrieval →
deterministic validation → three-state result → evidence drill-down → inspector
review/override → report generation — with graceful fallback to clearly-labeled
demo/cached data if the external AI service is unavailable.

"""Phase 2 database tests.

Two tiers, so the suite is meaningful even without a live PostgreSQL server:

1. **Schema-level tests** (always run, no DB connection needed) — verify
   every required table/column/relationship/constraint is registered on
   `Base.metadata` and that the ORM mapper configuration is internally
   consistent. These catch typos in column names, FK targets, and
   relationship wiring without needing Postgres at all.
2. **Live-DB integration tests** (skipped automatically if no database is
   reachable) — actually create the schema against a real PostgreSQL
   instance and round-trip a row through the ORM. Point `TEST_DATABASE_URL`
   at a throwaway database to run these; otherwise they're skipped, not
   failed, so `pytest` stays green in environments without Postgres (e.g.
   CI without a DB service, or a sandbox with no network).

Run just the schema-level tests anywhere:
    pytest tests/test_database.py -k "not live"

Run everything against a real database:
    export TEST_DATABASE_URL=postgresql+psycopg2://labelx:changeme@localhost:5432/labelx_test
    pytest tests/test_database.py
"""

from __future__ import annotations

import os
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, configure_mappers, sessionmaker

from database.base import Base
from database.enums import RuleVersionStatus, ScreeningStatus, UserRole
from database.models import (
    AuditLog,
    Declaration,
    Evidence,
    Image,
    OCRResult,
    RegulatoryRule,
    RuleVersion,
    Screening,
    User,
    ValidationResult,
)

EXPECTED_TABLES = {
    "users",
    "screenings",
    "images",
    "ocr_results",
    "declarations",
    "regulatory_rules",
    "rule_versions",
    "validation_results",
    "evidence",
    "audit_logs",
}


# ---------------------------------------------------------------------------
# Tier 1: schema-level tests — no database connection required.
# ---------------------------------------------------------------------------


def test_all_expected_tables_are_registered() -> None:
    assert EXPECTED_TABLES <= set(Base.metadata.tables.keys())


def test_mapper_configuration_is_consistent() -> None:
    """Fails loudly if any relationship() references a broken target/FK."""

    configure_mappers()


@pytest.mark.parametrize(
    "table_name",
    sorted(EXPECTED_TABLES),
)
def test_every_table_has_uuid_pk_and_timestamps(table_name: str) -> None:
    table = Base.metadata.tables[table_name]
    assert "id" in table.columns
    assert table.columns["id"].primary_key
    assert "created_at" in table.columns
    assert "updated_at" in table.columns


def test_foreign_keys_point_at_expected_tables() -> None:
    fk_targets = {
        ("screenings", "user_id"): "users",
        ("images", "screening_id"): "screenings",
        ("ocr_results", "image_id"): "images",
        ("declarations", "screening_id"): "screenings",
        ("rule_versions", "regulatory_rule_id"): "regulatory_rules",
        ("validation_results", "screening_id"): "screenings",
        ("validation_results", "declaration_id"): "declarations",
        ("validation_results", "rule_version_id"): "rule_versions",
        ("evidence", "validation_result_id"): "validation_results",
        ("evidence", "image_id"): "images",
        ("evidence", "ocr_result_id"): "ocr_results",
        ("audit_logs", "user_id"): "users",
        ("audit_logs", "screening_id"): "screenings",
    }
    for (table_name, column_name), expected_target in fk_targets.items():
        table = Base.metadata.tables[table_name]
        column = table.columns[column_name]
        assert column.foreign_keys, f"{table_name}.{column_name} should have a foreign key"
        target_table = next(iter(column.foreign_keys)).column.table.name
        assert target_table == expected_target


def test_regulatory_rule_uniqueness_constraint_present() -> None:
    table = Base.metadata.tables["regulatory_rules"]
    unique_col_sets = {
        tuple(sorted(c.name for c in constraint.columns))
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("rule_number", "sub_rule") in unique_col_sets


def test_rule_version_uniqueness_constraint_present() -> None:
    table = Base.metadata.tables["rule_versions"]
    unique_col_sets = {
        tuple(sorted(c.name for c in constraint.columns))
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("regulatory_rule_id", "version_number") in unique_col_sets


def test_rule_version_has_embedding_column() -> None:
    """The pgvector-prepared field required by Phase 2."""

    table = Base.metadata.tables["rule_versions"]
    assert "embedding" in table.columns
    assert table.columns["embedding"].nullable is True


def test_declaration_field_envelope_columns_present() -> None:
    table = Base.metadata.tables["declarations"]
    expected_fields = {
        "commodity_name",
        "manufacturer",
        "packer",
        "importer",
        "net_quantity_value",
        "net_quantity_unit",
        "mrp",
        "manufacture_date",
        "packing_date",
        "import_date",
        "consumer_complaint_contact",
        "dimensions",
        "other_declarations",
    }
    assert expected_fields <= set(table.columns.keys())


# ---------------------------------------------------------------------------
# Tier 2: live-database integration tests — auto-skipped if unreachable.
# ---------------------------------------------------------------------------


def _live_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set — skipping live-database tests")
    try:
        engine = create_engine(url, future=True)
        with engine.connect():
            pass
    except Exception as exc:  # noqa: BLE001 - any connection failure means "skip"
        pytest.skip(f"Could not connect to TEST_DATABASE_URL: {exc}")
    return engine


@pytest.fixture(scope="module")
def live_session():
    engine = _live_engine()
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_live_can_insert_and_read_back_a_full_chain(live_session: Session) -> None:
    user = User(email=f"test-{uuid.uuid4()}@labelx.local", full_name="Test User", role=UserRole.INSPECTOR)
    screening = Screening(user=user, status=ScreeningStatus.CREATED, category="Biscuits")
    image = Image(screening=screening, storage_path="/tmp/demo.jpg")
    declaration = Declaration(
        screening=screening,
        commodity_name={"value": "Biscuits", "present": True, "confidence": 0.95},
    )
    rule = RegulatoryRule(rule_number="6", sub_rule="1(c)", title="Net quantity declaration")
    rule_version = RuleVersion(
        regulatory_rule=rule,
        version_number=1,
        effective_from=date(2011, 4, 1),
        status=RuleVersionStatus.ACTIVE,
        enforced_text="Every package shall bear the net quantity declaration.",
    )

    live_session.add_all([user, screening, image, declaration, rule, rule_version])
    live_session.flush()

    validation_result = ValidationResult(
        screening=screening,
        declaration=declaration,
        rule_version=rule_version,
        result="needs_review",
    )
    live_session.add(validation_result)
    live_session.flush()

    evidence = Evidence(
        validation_result=validation_result,
        image=image,
        bbox={"x": 0, "y": 0, "w": 10, "h": 10},
    )
    audit_log = AuditLog(user=user, screening=screening, action="screening_created")
    live_session.add_all([evidence, audit_log])
    live_session.commit()

    fetched = live_session.get(Screening, screening.id)
    assert fetched is not None
    assert fetched.category == "Biscuits"
    assert len(fetched.images) == 1
    assert len(fetched.declarations) == 1
    assert len(fetched.validation_results) == 1
    assert fetched.validation_results[0].evidence_records[0].bbox == {
        "x": 0,
        "y": 0,
        "w": 10,
        "h": 10,
    }


def test_live_ocr_result_and_declaration_json_roundtrip(live_session: Session) -> None:
    screening = Screening(status=ScreeningStatus.CREATED)
    image = Image(screening=screening, storage_path="/tmp/demo2.jpg")
    ocr_result = OCRResult(
        image=image,
        engine="paddleocr",
        raw_text="NET WT 500g",
        tokens=[{"text": "500g", "bbox": [1, 2, 3, 4], "confidence": 0.9}],
        overall_confidence=0.9,
    )
    live_session.add_all([screening, image, ocr_result])
    live_session.commit()

    fetched = live_session.get(OCRResult, ocr_result.id)
    assert fetched is not None
    assert fetched.tokens[0]["text"] == "500g"

"""Phase 2 initial schema: all 10 database tables.

Hand-written to exactly mirror `database/models/`, since this project also
supports `database/init_db.py`'s `create_all()` path for local/demo use —
the two must produce an equivalent schema. Kept as a single revision because
Phase 2 introduces the whole schema at once; later phases should each add
their own incremental revision rather than editing this one.

Revision ID: 0001_initial_schema
Revises:
Create Date: (Phase 2)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from database.config import get_database_settings
from database.types import embedding_column

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    embedding_dim = get_database_settings().embedding_dim

    user_role = postgresql.ENUM("inspector", "admin", "viewer", name="user_role")
    screening_status = postgresql.ENUM(
        "created", "processing", "completed", "failed", name="screening_status"
    )
    screening_result = postgresql.ENUM(
        "no_obvious_issue",
        "needs_review",
        "potential_non_compliance",
        name="screening_result",
    )
    validation_result_state = postgresql.ENUM(
        "no_obvious_issue",
        "needs_review",
        "potential_non_compliance",
        name="validation_result_state",
    )
    rule_version_status = postgresql.ENUM(
        "active", "withdrawn", "amended", "superseded", name="rule_version_status"
    )

    bind = op.get_bind()
    for enum_type in (
        user_role,
        screening_status,
        screening_result,
        validation_result_state,
        rule_version_status,
    ):
        enum_type.create(bind, checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- regulatory_rules ---
    op.create_table(
        "regulatory_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("rule_number", sa.String(length=20), nullable=False),
        sa.Column("sub_rule", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("schedule_reference", sa.String(length=100), nullable=True),
        sa.Column("source_document", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("rule_number", "sub_rule", name="uq_regulatory_rules_rule_subrule"),
    )
    op.create_index("ix_regulatory_rules_rule_number", "regulatory_rules", ["rule_number"])

    # --- rule_versions ---
    op.create_table(
        "rule_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "regulatory_rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("regulatory_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("status", rule_version_status, nullable=False),
        sa.Column("citation", sa.String(length=500), nullable=True),
        sa.Column("enforced_text", sa.Text(), nullable=False),
        sa.Column("embedding", embedding_column(embedding_dim), nullable=True),
        sa.UniqueConstraint(
            "regulatory_rule_id", "version_number", name="uq_rule_versions_rule_version_number"
        ),
    )
    op.create_index("ix_rule_versions_regulatory_rule_id", "rule_versions", ["regulatory_rule_id"])
    op.create_index(
        "ix_rule_versions_effective_range", "rule_versions", ["effective_from", "effective_to"]
    )
    op.create_index("ix_rule_versions_status", "rule_versions", ["status"])

    # --- screenings ---
    op.create_table(
        "screenings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", screening_status, nullable=False),
        sa.Column("overall_result", screening_result, nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_screenings_user_id", "screenings", ["user_id"])
    op.create_index("ix_screenings_status", "screenings", ["status"])
    op.create_index("ix_screenings_status_created_at", "screenings", ["status", "created_at"])

    # --- images ---
    op.create_table(
        "images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "screening_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("screenings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("width_px", sa.Integer(), nullable=True),
        sa.Column("height_px", sa.Integer(), nullable=True),
        sa.Column("is_principal_display_panel", sa.Boolean(), nullable=True),
    )
    op.create_index("ix_images_screening_id", "images", ["screening_id"])

    # --- ocr_results ---
    op.create_table(
        "ocr_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "image_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("images.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("engine", sa.String(length=50), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("tokens", postgresql.JSONB(), nullable=True),
        sa.Column("overall_confidence", sa.Float(), nullable=True),
    )
    op.create_index("ix_ocr_results_image_id", "ocr_results", ["image_id"])

    # --- declarations ---
    op.create_table(
        "declarations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "screening_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("screenings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("commodity_name", postgresql.JSONB(), nullable=True),
        sa.Column("manufacturer", postgresql.JSONB(), nullable=True),
        sa.Column("packer", postgresql.JSONB(), nullable=True),
        sa.Column("importer", postgresql.JSONB(), nullable=True),
        sa.Column("net_quantity_value", postgresql.JSONB(), nullable=True),
        sa.Column("net_quantity_unit", postgresql.JSONB(), nullable=True),
        sa.Column("mrp", postgresql.JSONB(), nullable=True),
        sa.Column("manufacture_date", postgresql.JSONB(), nullable=True),
        sa.Column("packing_date", postgresql.JSONB(), nullable=True),
        sa.Column("import_date", postgresql.JSONB(), nullable=True),
        sa.Column("consumer_complaint_contact", postgresql.JSONB(), nullable=True),
        sa.Column("dimensions", postgresql.JSONB(), nullable=True),
        sa.Column("other_declarations", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_declarations_screening_id", "declarations", ["screening_id"])

    # --- validation_results ---
    op.create_table(
        "validation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "screening_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("screenings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "declaration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("declarations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "rule_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rule_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("result", validation_result_state, nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_validation_results_screening_id", "validation_results", ["screening_id"])
    op.create_index(
        "ix_validation_results_rule_version_id", "validation_results", ["rule_version_id"]
    )
    op.create_index("ix_validation_results_result", "validation_results", ["result"])

    # --- evidence ---
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "validation_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("validation_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "image_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("images.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "ocr_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ocr_results.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("bbox", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_evidence_validation_result_id", "evidence", ["validation_result_id"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "screening_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("screenings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_screening_created_at", "audit_logs", ["screening_id", "created_at"])
    op.create_index("ix_audit_logs_user_created_at", "audit_logs", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("evidence")
    op.drop_table("validation_results")
    op.drop_table("declarations")
    op.drop_table("ocr_results")
    op.drop_table("images")
    op.drop_table("screenings")
    op.drop_table("rule_versions")
    op.drop_table("regulatory_rules")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_name in (
        "rule_version_status",
        "validation_result_state",
        "screening_result",
        "screening_status",
        "user_role",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)

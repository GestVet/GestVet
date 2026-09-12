"""crear los adjuntos.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clinical_entry_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=150), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(length=300), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_entry_id"],
            ["clinical_entries.id"],
            name="fk_attachments_clinical_entry",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"], ["users.id"], name="fk_attachments_uploaded_by", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_attachments_clinical_entry_id", "attachments", ["clinical_entry_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_attachments_clinical_entry_id", table_name="attachments")
    op.drop_table("attachments")

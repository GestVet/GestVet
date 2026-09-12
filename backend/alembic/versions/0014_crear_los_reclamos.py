"""crear los reclamos.

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("veterinarian_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["client_id"], ["users.id"], name="fk_complaints_client", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["veterinarian_id"],
            ["users.id"],
            name="fk_complaints_veterinarian",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_complaints_appointment",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaints_client_id", "complaints", ["client_id"], unique=False)
    op.create_index(
        "ix_complaints_veterinarian_id", "complaints", ["veterinarian_id"], unique=False
    )
    op.create_index("ix_complaints_appointment_id", "complaints", ["appointment_id"], unique=False)

    op.create_table(
        "complaint_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=150), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(length=300), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["complaint_id"],
            ["complaints.id"],
            name="fk_complaint_evidence_complaint",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["users.id"],
            name="fk_complaint_evidence_uploaded_by",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_complaint_evidence_complaint_id", "complaint_evidence", ["complaint_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_complaint_evidence_complaint_id", table_name="complaint_evidence")
    op.drop_table("complaint_evidence")
    op.drop_index("ix_complaints_appointment_id", table_name="complaints")
    op.drop_index("ix_complaints_veterinarian_id", table_name="complaints")
    op.drop_index("ix_complaints_client_id", table_name="complaints")
    op.drop_table("complaints")

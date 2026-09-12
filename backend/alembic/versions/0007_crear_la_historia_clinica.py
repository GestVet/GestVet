"""crear la historia clinica.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinical_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("veterinarian_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("diagnosis", sa.String(length=300), nullable=False),
        sa.Column("treatment", sa.String(length=300), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_clinical_entries_appointment",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["pet_id"], ["pets.id"], name="fk_clinical_entries_pet", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["veterinarian_id"],
            ["users.id"],
            name="fk_clinical_entries_veterinarian",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clinical_entries_pet_id", "clinical_entries", ["pet_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_clinical_entries_pet_id", table_name="clinical_entries")
    op.drop_table("clinical_entries")

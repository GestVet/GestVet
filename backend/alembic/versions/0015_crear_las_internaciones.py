"""crear las internaciones.

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hospitalizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("opened_by", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("discharge_notes", sa.String(length=1000), nullable=False),
        sa.Column("admitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discharged_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_hospitalizations_appointment",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["pet_id"], ["pets.id"], name="fk_hospitalizations_pet", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["opened_by"], ["users.id"], name="fk_hospitalizations_opened_by", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_hospitalizations_appointment_id", "hospitalizations", ["appointment_id"], unique=False
    )
    op.create_index("ix_hospitalizations_pet_id", "hospitalizations", ["pet_id"], unique=False)
    op.create_index("ix_hospitalizations_status", "hospitalizations", ["status"], unique=False)

    op.create_table(
        "hospitalization_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hospitalization_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["hospitalization_id"],
            ["hospitalizations.id"],
            name="fk_hospitalization_notes_hospitalization",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name="fk_hospitalization_notes_author",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_hospitalization_notes_hospitalization_id",
        "hospitalization_notes",
        ["hospitalization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_hospitalization_notes_hospitalization_id", table_name="hospitalization_notes")
    op.drop_table("hospitalization_notes")
    op.drop_index("ix_hospitalizations_status", table_name="hospitalizations")
    op.drop_index("ix_hospitalizations_pet_id", table_name="hospitalizations")
    op.drop_index("ix_hospitalizations_appointment_id", table_name="hospitalizations")
    op.drop_table("hospitalizations")

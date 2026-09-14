"""crear el carnet de vacunas.

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-14

Cada vacuna aplicada, con su producto, lote y próxima dosis. Hasta ahora una
vacuna era una entrada más de la historia clínica con texto libre, sin forma de
saber cuándo tocaba la siguiente.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pet_vaccinations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("veterinarian_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("vaccine", sa.String(length=30), nullable=False),
        sa.Column("applied_on", sa.Date(), nullable=False),
        sa.Column("next_due_on", sa.Date(), nullable=True),
        sa.Column("product_name", sa.String(length=80), nullable=False),
        sa.Column("batch", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.String(length=300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["pet_id"], ["pets.id"], name="fk_pet_vaccinations_pet", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["veterinarian_id"],
            ["users.id"],
            name="fk_pet_vaccinations_veterinarian",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_pet_vaccinations_appointment",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pet_vaccinations_pet_id", "pet_vaccinations", ["pet_id"], unique=False)
    op.create_index(
        "ix_pet_vaccinations_next_due_on", "pet_vaccinations", ["next_due_on"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_pet_vaccinations_next_due_on", table_name="pet_vaccinations")
    op.drop_index("ix_pet_vaccinations_pet_id", table_name="pet_vaccinations")
    op.drop_table("pet_vaccinations")

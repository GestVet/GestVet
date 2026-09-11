"""crear la tabla de disponibilidad.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "availability_slots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("veterinarian_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["veterinarian_id"],
            ["users.id"],
            name="fk_slots_veterinarian",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_availability_slots_veterinarian_id",
        "availability_slots",
        ["veterinarian_id"],
        unique=False,
    )
    # Toda consulta de agenda pregunta por un veterinario y un rango de fechas.
    op.create_index(
        "ix_slots_veterinarian_window",
        "availability_slots",
        ["veterinarian_id", "starts_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_slots_veterinarian_window", table_name="availability_slots")
    op.drop_index("ix_availability_slots_veterinarian_id", table_name="availability_slots")
    op.drop_table("availability_slots")

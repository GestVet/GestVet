"""avisar por WhatsApp las vacunas por vencer.

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-14

Guarda cuándo se le avisó al dueño que a su mascota le toca la próxima dosis,
para que el proceso periódico no repita el mensaje en cada vuelta.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pet_vaccinations",
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # En lote: SQLite no borra columnas con un ALTER TABLE simple.
    with op.batch_alter_table("pet_vaccinations") as batch:
        batch.drop_column("reminder_sent_at")

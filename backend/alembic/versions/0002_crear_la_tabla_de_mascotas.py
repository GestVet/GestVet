"""crear la tabla de mascotas.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("species", sa.String(length=40), nullable=False),
        sa.Column("breed", sa.String(length=60), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_pets_owner", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # El listado de un cliente siempre filtra por dueno, y el informe de la
    # clinica agrupa por especie.
    op.create_index("ix_pets_owner_id", "pets", ["owner_id"], unique=False)
    op.create_index("ix_pets_species", "pets", ["species"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pets_species", table_name="pets")
    op.drop_index("ix_pets_owner_id", table_name="pets")
    op.drop_table("pets")

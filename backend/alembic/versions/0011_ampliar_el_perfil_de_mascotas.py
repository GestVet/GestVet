"""ampliar el perfil de mascotas.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pets", sa.Column("sex", sa.String(length=10), nullable=True))
    op.add_column(
        "pets", sa.Column("color", sa.String(length=80), nullable=False, server_default="")
    )
    op.add_column(
        "pets",
        sa.Column("microchip_number", sa.String(length=40), nullable=False, server_default=""),
    )
    op.add_column(
        "pets", sa.Column("temperament", sa.String(length=120), nullable=False, server_default="")
    )
    op.add_column("pets", sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column("pets", sa.Column("height_cm", sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column("pets", sa.Column("is_sterilized", sa.Boolean(), nullable=True))
    op.add_column(
        "pets", sa.Column("allergies", sa.String(length=300), nullable=False, server_default="")
    )


def downgrade() -> None:
    op.drop_column("pets", "allergies")
    op.drop_column("pets", "is_sterilized")
    op.drop_column("pets", "height_cm")
    op.drop_column("pets", "weight_kg")
    op.drop_column("pets", "temperament")
    op.drop_column("pets", "microchip_number")
    op.drop_column("pets", "color")
    op.drop_column("pets", "sex")

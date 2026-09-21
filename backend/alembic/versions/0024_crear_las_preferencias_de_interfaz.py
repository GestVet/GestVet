"""crear las preferencias de interfaz de usuario.

Revision ID: 0024
Revises: 0023
Create Date: 2026-09-21

Tabla `user_layout_preferences` para almacenar el orden del menú lateral y la
visibilidad/orden de los bloques del panel principal de cada usuario.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_layout_preferences",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sidebar_order", sa.JSON(), nullable=False),
        sa.Column("dashboard_blocks", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_layout_preferences_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_layout_preferences")

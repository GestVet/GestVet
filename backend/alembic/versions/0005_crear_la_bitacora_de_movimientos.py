"""crear la bitacora de movimientos.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "activity_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("detail", sa.String(length=200), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        # RESTRICT y no CASCADE: si borrar una cuenta se llevara sus asientos,
        # la bitacora dejaria de servir justo para lo que existe.
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_activity_user", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_log_user_id", "activity_log", ["user_id"], unique=False)
    op.create_index("ix_activity_log_kind", "activity_log", ["kind"], unique=False)
    # La pantalla pide los ultimos movimientos de un conjunto de cuentas.
    op.create_index(
        "ix_activity_user_moment", "activity_log", ["user_id", "occurred_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_activity_user_moment", table_name="activity_log")
    op.drop_index("ix_activity_log_kind", table_name="activity_log")
    op.drop_index("ix_activity_log_user_id", table_name="activity_log")
    op.drop_table("activity_log")

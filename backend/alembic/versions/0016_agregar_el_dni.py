"""agregar el dni.

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("document_id", sa.String(length=8), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("users", "document_id")

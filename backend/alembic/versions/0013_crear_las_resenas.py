"""crear las resenas.

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("veterinarian_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["veterinarian_id"], ["users.id"], name="fk_reviews_veterinarian", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["users.id"], name="fk_reviews_client", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("veterinarian_id", "client_id", name="uq_reviews_vet_client"),
    )
    op.create_index("ix_reviews_veterinarian_id", "reviews", ["veterinarian_id"], unique=False)
    op.create_index("ix_reviews_client_id", "reviews", ["client_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reviews_client_id", table_name="reviews")
    op.drop_index("ix_reviews_veterinarian_id", table_name="reviews")
    op.drop_table("reviews")

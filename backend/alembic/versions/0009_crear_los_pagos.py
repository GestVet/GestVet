"""crear los pagos.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("registered_by", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("reference", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.String(length=300), nullable=False),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("void_reason", sa.String(length=300), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_payments_appointment",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["users.id"], name="fk_payments_client", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["registered_by"], ["users.id"], name="fk_payments_registered_by", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_appointment_id", "payments", ["appointment_id"], unique=False)
    op.create_index("ix_payments_client_id", "payments", ["client_id"], unique=False)
    op.create_index("ix_payments_method", "payments", ["method"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payments_method", table_name="payments")
    op.drop_index("ix_payments_client_id", table_name="payments")
    op.drop_index("ix_payments_appointment_id", table_name="payments")
    op.drop_table("payments")

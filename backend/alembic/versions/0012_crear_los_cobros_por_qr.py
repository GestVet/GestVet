"""crear los cobros por qr.

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "qr_charges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("gateway_charge_id", sa.String(length=120), nullable=False),
        sa.Column("qr_image_data_url", sa.Text(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_qr_charges_appointment",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["users.id"], name="fk_qr_charges_client", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], name="fk_qr_charges_payment", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qr_charges_appointment_id", "qr_charges", ["appointment_id"], unique=False)
    op.create_index("ix_qr_charges_client_id", "qr_charges", ["client_id"], unique=False)
    op.create_index("ix_qr_charges_status", "qr_charges", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_qr_charges_status", table_name="qr_charges")
    op.drop_index("ix_qr_charges_client_id", table_name="qr_charges")
    op.drop_index("ix_qr_charges_appointment_id", table_name="qr_charges")
    op.drop_table("qr_charges")

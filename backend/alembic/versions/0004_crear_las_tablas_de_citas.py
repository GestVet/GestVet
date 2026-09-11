"""crear las tablas de citas y sembrar los motivos de consulta.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-10
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Los motivos de consulta son datos de referencia, no datos de usuario: el
# sistema no funciona sin ellos, y la emergencia en particular es la que el
# alta automatica busca. Por eso se siembran en la migracion.
#
# El original tambien los tenia en tabla, pero marcaba la emergencia con el
# identificador 8 escrito a mano en media docena de consultas. Aca la marca es
# la columna is_emergency y el identificador deja de significar nada.
MOTIVOS: list[tuple[str, int, str, bool]] = [
    ("Consulta general", 30, "60.00", False),
    ("Vacunacion", 20, "45.00", False),
    ("Desparasitacion", 20, "40.00", False),
    ("Control post operatorio", 20, "35.00", False),
    ("Cirugia menor", 90, "350.00", False),
    ("Bano y estetica", 60, "55.00", False),
    ("Analisis de laboratorio", 30, "80.00", False),
    ("Emergencia", 60, "150.00", True),
]


def upgrade() -> None:
    tipos = op.create_table(
        "appointment_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("is_emergency", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "ix_appointment_types_is_emergency", "appointment_types", ["is_emergency"], unique=False
    )

    op.bulk_insert(
        tipos,
        [
            {
                "name": nombre,
                "duration_minutes": minutos,
                "price": Decimal(precio),
                "is_emergency": emergencia,
                "is_active": True,
            }
            for nombre, minutos, precio, emergencia in MOTIVOS
        ],
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("veterinarian_id", sa.Integer(), nullable=False),
        sa.Column("appointment_type_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("cancellation_reason", sa.String(length=300), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["appointment_type_id"],
            ["appointment_types.id"],
            name="fk_appointments_type",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["users.id"], name="fk_appointments_client", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["pet_id"], ["pets.id"], name="fk_appointments_pet", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], name="fk_appointments_updated_by", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["veterinarian_id"],
            ["users.id"],
            name="fk_appointments_veterinarian",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_appointments_client_id", "appointments", ["client_id"], unique=False)
    op.create_index("ix_appointments_pet_id", "appointments", ["pet_id"], unique=False)
    op.create_index("ix_appointments_scheduled_at", "appointments", ["scheduled_at"], unique=False)
    op.create_index("ix_appointments_status", "appointments", ["status"], unique=False)
    op.create_index(
        "ix_appointments_veterinarian_id", "appointments", ["veterinarian_id"], unique=False
    )
    # La comprobacion de solapamiento pregunta por un veterinario y una ventana
    # de tiempo en cada alta.
    op.create_index(
        "ix_appointments_veterinarian_window",
        "appointments",
        ["veterinarian_id", "scheduled_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_veterinarian_window", table_name="appointments")
    op.drop_index("ix_appointments_veterinarian_id", table_name="appointments")
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_scheduled_at", table_name="appointments")
    op.drop_index("ix_appointments_pet_id", table_name="appointments")
    op.drop_index("ix_appointments_client_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_index("ix_appointment_types_is_emergency", table_name="appointment_types")
    op.drop_table("appointment_types")

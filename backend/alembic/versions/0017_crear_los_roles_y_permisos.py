"""crear los roles y permisos.

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-13

Siembra un rol de sistema por tipo de cuenta con los permisos que la aplicación
daba antes de existir los roles editables, así una base migrada se comporta
igual que antes. La lista está escrita acá y no importada del código: una
migración tiene que seguir haciendo lo mismo aunque el catálogo cambie después.
Una prueba compara esta semilla con la del código.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COMUNES = (
    "appointments.read",
    "appointments.cancel",
    "schedule.read",
    "veterinarians.read",
    "payments.read",
    "payments.qr",
    "complaints.read",
    "hospitalizations.read",
    "clinical_records.read",
    "reviews.read",
)
_MOSTRADOR = (
    "pets.register_for_owner",
    "pets.read_any",
    "pets.correct_status",
    "emergencies.open_walk_in",
    "payments.register",
    "payments.void",
    "clients.read",
    "clients.register_walk_in",
    "clients.update_contact",
)
_VETERINARIO = (
    *_COMUNES,
    *_MOSTRADOR,
    "appointments.attend",
    "schedule.manage_own",
    "hospitalizations.manage",
    "clinical_records.write",
    "pets.edit_clinical_profile",
)

_ROLES_DE_SISTEMA: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "admin",
        "Administración",
        (
            *_COMUNES,
            *_MOSTRADOR,
            "payments.report",
            "staff.read",
            "staff.manage",
            "users.change_status",
            "activity.read",
            "insights.read",
            "roles.manage",
        ),
    ),
    (
        "client",
        "Cliente",
        (
            *_COMUNES,
            "pets.manage_own",
            "appointments.book",
            "emergencies.open",
            "complaints.file",
            "reviews.submit",
        ),
    ),
    ("veterinarian", "Veterinario", _VETERINARIO),
    ("emergency_veterinarian", "Veterinario de guardia", _VETERINARIO),
)


def upgrade() -> None:
    roles = op.create_table(
        "access_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("account_kind", sa.String(length=32), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_access_roles_name", "access_roles", ["name"], unique=True)
    op.create_index("ix_access_roles_account_kind", "access_roles", ["account_kind"], unique=False)

    permisos = op.create_table(
        "access_role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["access_roles.id"],
            name="fk_access_role_permissions_role",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission"),
    )

    op.create_table(
        "user_access_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_access_roles_user", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["access_roles.id"], name="fk_user_access_roles_role", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_user_access_roles_role_id", "user_access_roles", ["role_id"], unique=False)

    ahora = datetime.now(UTC)
    op.bulk_insert(
        roles,
        [
            {
                "name": nombre,
                "description": "",
                "account_kind": tipo,
                "is_system": True,
                "created_at": ahora,
            }
            for tipo, nombre, _ in _ROLES_DE_SISTEMA
        ],
    )
    conexion = op.get_bind()
    for tipo, _, codigos in _ROLES_DE_SISTEMA:
        role_id = conexion.execute(
            sa.text("SELECT id FROM access_roles WHERE account_kind = :tipo AND is_system = :si"),
            {"tipo": tipo, "si": True},
        ).scalar_one()
        op.bulk_insert(
            permisos, [{"role_id": role_id, "permission": codigo} for codigo in sorted(codigos)]
        )


def downgrade() -> None:
    op.drop_index("ix_user_access_roles_role_id", table_name="user_access_roles")
    op.drop_table("user_access_roles")
    op.drop_table("access_role_permissions")
    op.drop_index("ix_access_roles_account_kind", table_name="access_roles")
    op.drop_index("ix_access_roles_name", table_name="access_roles")
    op.drop_table("access_roles")

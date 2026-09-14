"""asignar turnos y guardias.

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-13

Los turnos pasan a asignarlos la clínica y la guardia deja de ser un rol para
ser un tipo de turno:

- cada tramo de agenda gana `kind` (atención o guardia) y quién lo asignó;
- las cuentas con rol de veterinario de guardia pasan a veterinario, y sus
  tramos pasan a ser guardias, así nadie pierde la cobertura que tenía;
- desaparece el respaldo de emergencias: ahora cubre quien esté en turno;
- el permiso de publicar la agenda propia se reemplaza por ver los turnos
  propios y pedir cambios, y la administración gana el de asignarlos;
- se crea la tabla de pedidos de cambio de turno.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_GUARDIA = "emergency_veterinarian"
_VETERINARIO = "veterinarian"
_PERMISO_ANTERIOR = "schedule.manage_own"
_PERMISOS_DEL_VETERINARIO = ("schedule.read_own", "schedule.request_change")
_PERMISO_DE_ADMINISTRACION = "schedule.manage"


def _turnos() -> None:
    with op.batch_alter_table("availability_slots") as batch:
        batch.add_column(
            sa.Column("kind", sa.String(length=16), nullable=False, server_default="regular")
        )
        batch.add_column(sa.Column("assigned_by_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_slots_assigned_by", "users", ["assigned_by_id"], ["id"], ondelete="SET NULL"
        )
    op.execute(
        sa.text(
            "UPDATE availability_slots SET kind = 'on_call' "
            "WHERE veterinarian_id IN (SELECT id FROM users WHERE role = :guardia)"
        ).bindparams(guardia=_GUARDIA)
    )


def _cuentas() -> None:
    op.execute(
        sa.text("UPDATE users SET role = :veterinario WHERE role = :guardia").bindparams(
            veterinario=_VETERINARIO, guardia=_GUARDIA
        )
    )
    with op.batch_alter_table("users") as batch:
        batch.drop_column("can_cover_emergencies")


def _roles(conexion: sa.Connection) -> None:
    sistema_de_guardia = (
        conexion.execute(
            sa.text(
                "SELECT id FROM access_roles WHERE account_kind = :guardia AND is_system = :si"
            ),
            {"guardia": _GUARDIA, "si": True},
        )
        .scalars()
        .all()
    )
    for role_id in sistema_de_guardia:
        conexion.execute(
            sa.text("DELETE FROM user_access_roles WHERE role_id = :id"), {"id": role_id}
        )
        conexion.execute(
            sa.text("DELETE FROM access_role_permissions WHERE role_id = :id"), {"id": role_id}
        )
        conexion.execute(sa.text("DELETE FROM access_roles WHERE id = :id"), {"id": role_id})
    # Un rol propio de guardia tenía los mismos permisos posibles que uno de
    # veterinario, así que basta con cambiarle el tipo de cuenta.
    conexion.execute(
        sa.text(
            "UPDATE access_roles SET account_kind = :veterinario WHERE account_kind = :guardia"
        ),
        {"veterinario": _VETERINARIO, "guardia": _GUARDIA},
    )


def _permisos(conexion: sa.Connection) -> None:
    con_agenda = set(
        conexion.execute(
            sa.text("SELECT role_id FROM access_role_permissions WHERE permission = :permiso"),
            {"permiso": _PERMISO_ANTERIOR},
        ).scalars()
    )
    sistema = {
        row[0]: row[1]
        for row in conexion.execute(
            sa.text("SELECT account_kind, id FROM access_roles WHERE is_system = :si"),
            {"si": True},
        ).all()
    }
    conexion.execute(
        sa.text("DELETE FROM access_role_permissions WHERE permission = :permiso"),
        {"permiso": _PERMISO_ANTERIOR},
    )

    agregar: set[tuple[int, str]] = set()
    if _VETERINARIO in sistema:
        con_agenda.add(sistema[_VETERINARIO])
    for role_id in con_agenda:
        agregar.update((role_id, permiso) for permiso in _PERMISOS_DEL_VETERINARIO)
    if "admin" in sistema:
        agregar.add((sistema["admin"], _PERMISO_DE_ADMINISTRACION))

    existentes = {
        tuple(row)
        for row in conexion.execute(
            sa.text("SELECT role_id, permission FROM access_role_permissions")
        ).all()
    }
    for role_id, permiso in sorted(agregar - existentes):
        conexion.execute(
            sa.text(
                "INSERT INTO access_role_permissions (role_id, permission) VALUES (:id, :permiso)"
            ),
            {"id": role_id, "permiso": permiso},
        )


def _pedidos() -> None:
    op.create_table(
        "shift_change_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("veterinarian_id", sa.Integer(), nullable=False),
        sa.Column("slot_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("response", sa.String(length=500), nullable=False),
        sa.Column("resolved_by_id", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["veterinarian_id"],
            ["users.id"],
            name="fk_shift_change_requests_veterinarian",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["availability_slots.id"],
            name="fk_shift_change_requests_slot",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_id"],
            ["users.id"],
            name="fk_shift_change_requests_resolver",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_shift_change_requests_veterinarian_id",
        "shift_change_requests",
        ["veterinarian_id"],
        unique=False,
    )
    op.create_index(
        "ix_shift_change_requests_status", "shift_change_requests", ["status"], unique=False
    )


def upgrade() -> None:
    conexion = op.get_bind()
    _turnos()
    _cuentas()
    _roles(conexion)
    _permisos(conexion)
    _pedidos()


def downgrade() -> None:
    # Vuelve la estructura, no los datos: qué veterinario era "de guardia" ya no
    # se puede deducir de una cuenta, y los roles de guardia borrados no vuelven.
    op.drop_index("ix_shift_change_requests_status", table_name="shift_change_requests")
    op.drop_index("ix_shift_change_requests_veterinarian_id", table_name="shift_change_requests")
    op.drop_table("shift_change_requests")
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "can_cover_emergencies", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
    with op.batch_alter_table("availability_slots") as batch:
        batch.drop_constraint("fk_slots_assigned_by", type_="foreignkey")
        batch.drop_column("assigned_by_id")
        batch.drop_column("kind")

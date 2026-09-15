"""agregar el panorama de mascotas.

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-15

Nuevo permiso `pets.overview_read`: administración ve todas las mascotas de
la clínica, veterinario solo las que atendió. Se agrega a los roles de
sistema `admin` y `veterinarian` ya sembrados por la migración 0017, con la
misma técnica que ya usó la 0020 para `pets.manage_catalog`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISO = "pets.overview_read"
_ROLES = ("admin", "veterinarian")


def upgrade() -> None:
    conexion = op.get_bind()
    for tipo in _ROLES:
        role_id = conexion.execute(
            sa.text("SELECT id FROM access_roles WHERE account_kind = :tipo AND is_system = :si"),
            {"tipo": tipo, "si": True},
        ).scalar_one_or_none()
        if role_id is not None:
            conexion.execute(
                sa.text(
                    "INSERT INTO access_role_permissions (role_id, permission) "
                    "VALUES (:rol, :permiso)"
                ),
                {"rol": role_id, "permiso": PERMISO},
            )


def downgrade() -> None:
    op.execute(sa.text(f"DELETE FROM access_role_permissions WHERE permission = '{PERMISO}'"))

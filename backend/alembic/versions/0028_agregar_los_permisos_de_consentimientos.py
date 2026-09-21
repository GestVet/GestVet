"""agregar los permisos de consentimientos.

Revision ID: 0028
Revises: 0027
Create Date: 2026-09-21

Dos permisos nuevos, sembrados en los roles de sistema con la misma técnica
que la 0023:

- `consents.request`, al veterinario: pedir un consentimiento, tomar la firma
  en persona y atender sin consentimiento por urgencia vital;
- `consents.respond`, al cliente: aceptar o rechazar los pedidos sobre sus
  mascotas.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PERMISOS_POR_ROL = (
    ("veterinarian", "consents.request"),
    ("client", "consents.respond"),
)


def upgrade() -> None:
    conexion = op.get_bind()
    for tipo, permiso in _PERMISOS_POR_ROL:
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
                {"rol": role_id, "permiso": permiso},
            )


def downgrade() -> None:
    for _, permiso in _PERMISOS_POR_ROL:
        op.execute(sa.text(f"DELETE FROM access_role_permissions WHERE permission = '{permiso}'"))

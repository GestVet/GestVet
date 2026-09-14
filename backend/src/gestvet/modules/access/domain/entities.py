"""Entidades de dominio de accesos.

Python puro. Un rol agrupa permisos del catálogo del núcleo y pertenece a un
tipo de cuenta: un rol para veterinarios no puede asignarse a un cliente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from gestvet.core.identity import Role
from gestvet.core.permissions import (
    CATALOG,
    PROTECTED_ADMIN_PERMISSIONS,
    Permission,
    allowed_for,
)
from gestvet.modules.access.domain.exceptions import AccessRoleLocked, InvalidAccessRole

MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 60
MAX_DESCRIPTION_LENGTH = 200


def parse_permissions(codes: frozenset[str] | set[str] | list[str]) -> frozenset[Permission]:
    """Convierte códigos en permisos, rechazando los que el catálogo no conoce."""
    desconocidos = sorted(code for code in codes if code not in Permission.__members__.values())
    if desconocidos:
        raise InvalidAccessRole(f"Permisos desconocidos: {', '.join(desconocidos)}.")
    return frozenset(Permission(code) for code in codes)


@dataclass(slots=True)
class AccessRole:
    name: str
    account_kind: Role
    permissions: frozenset[Permission]
    description: str = ""
    is_system: bool = False
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.name = " ".join(self.name.split())
        if not MIN_NAME_LENGTH <= len(self.name) <= MAX_NAME_LENGTH:
            raise InvalidAccessRole(
                f"El nombre del rol debe tener entre {MIN_NAME_LENGTH} y "
                f"{MAX_NAME_LENGTH} caracteres."
            )
        self.description = self.description.strip()
        if len(self.description) > MAX_DESCRIPTION_LENGTH:
            raise InvalidAccessRole(
                f"La descripción admite {MAX_DESCRIPTION_LENGTH} caracteres como máximo."
            )
        self._ensure_permissions_fit_the_kind()
        self._ensure_admin_keeps_control()

    def _ensure_permissions_fit_the_kind(self) -> None:
        # Un permiso que el tipo de cuenta no puede usar confundiría a quien
        # arma el rol: aparecería marcado y nunca haría nada.
        fuera = self.permissions - allowed_for(self.account_kind)
        if fuera:
            nombres = ", ".join(sorted(CATALOG[permission].label for permission in fuera))
            raise InvalidAccessRole(
                f"Estos permisos no aplican a cuentas de tipo {self.account_kind.label}: {nombres}."
            )

    def _ensure_admin_keeps_control(self) -> None:
        if self.is_system and self.account_kind is Role.ADMIN:
            faltan = PROTECTED_ADMIN_PERMISSIONS - self.permissions
            if faltan:
                raise AccessRoleLocked(
                    "El rol de sistema de administración no puede perder el permiso de "
                    "administrar roles."
                )

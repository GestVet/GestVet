"""Entidades de dominio de cuentas.

Python puro. Sin FastAPI, sin SQLAlchemy, sin Pydantic. Este archivo debe
poder ejecutarse sin que exista una base de datos ni un servidor web, y los
contratos de Import Linter lo verifican.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

# El rol vive en el núcleo compartido, no acá: lo necesitan todos los módulos
# para autorizar, y si lo poseyera `accounts` todos tendrían que importarlo.
from gestvet.core.identity import Role
from gestvet.modules.accounts.domain.exceptions import (
    InvalidEmail,
    RoleNotAssignable,
    RoleNotSelfAssignable,
    RoleNotSwappable,
)

# El hallazgo P0 de la auditoría de CitasVet fue que un visitante podía pedir
# rol de administrador al registrarse. La regla vive aquí, en el dominio, para
# que ningún adaptador pueda saltársela aceptando un rol del cuerpo HTTP.
SELF_ASSIGNABLE_ROLES: frozenset[Role] = frozenset({Role.CLIENT})

# Roles que la administración puede dar de alta. No incluye ADMIN: una cuenta
# de administración se siembra, no se crea desde una pantalla.
STAFF_ASSIGNABLE_ROLES: frozenset[Role] = frozenset(
    {Role.VETERINARIAN, Role.EMERGENCY_VETERINARIAN}
)

# La guardia se da y se quita, y eso es todo lo que este cambio permite. El
# original tenía un endpoint que aceptaba cualquier rol destino, así que servía
# para convertir a un cliente en administrador.
ROLE_SWAPS: dict[Role, Role] = {
    Role.VETERINARIAN: Role.EMERGENCY_VETERINARIAN,
    Role.EMERGENCY_VETERINARIAN: Role.VETERINARIAN,
}


@dataclass(slots=True)
class User:
    email: str
    first_name: str
    last_name: str
    role: Role
    password_hash: str
    phone: str = ""
    is_active: bool = True
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.email = normalize_email(self.email)

    @property
    def full_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.email

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True


def normalize_email(raw: str) -> str:
    email = raw.strip().lower()
    local, separator, domain = email.partition("@")
    if not separator or not local or "." not in domain:
        raise InvalidEmail(raw)
    return email


def ensure_role_is_self_assignable(role: Role) -> None:
    if role not in SELF_ASSIGNABLE_ROLES:
        raise RoleNotSelfAssignable(role.value)


def ensure_role_is_staff_assignable(role: Role) -> None:
    if role not in STAFF_ASSIGNABLE_ROLES:
        raise RoleNotAssignable(role.value)


def swapped_guard_role(role: Role) -> Role:
    target = ROLE_SWAPS.get(role)
    if target is None:
        raise RoleNotSwappable(role.value)
    return target

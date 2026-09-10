"""Entidades de dominio de cuentas.

Python puro. Sin FastAPI, sin SQLAlchemy, sin Pydantic. Este archivo debe
poder ejecutarse sin que exista una base de datos ni un servidor web, y los
contratos de Import Linter lo verifican.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from gestvet.accounts.domain.exceptions import (
    InvalidEmail,
    PermissionDenied,
    RoleNotSelfAssignable,
)


class Role(StrEnum):
    ADMIN = "admin"
    CLIENT = "client"
    VETERINARIAN = "veterinarian"
    EMERGENCY_VETERINARIAN = "emergency_veterinarian"

    @property
    def label(self) -> str:
        return _ROLE_LABELS[self]


_ROLE_LABELS: dict[Role, str] = {
    Role.ADMIN: "Administrador",
    Role.CLIENT: "Cliente",
    Role.VETERINARIAN: "Veterinario",
    Role.EMERGENCY_VETERINARIAN: "Veterinario de emergencia",
}

# El hallazgo P0 de la auditoría de CitasVet fue que un visitante podía pedir
# rol de administrador al registrarse. La regla vive aquí, en el dominio, para
# que ningún adaptador pueda saltársela aceptando un rol del cuerpo HTTP.
SELF_ASSIGNABLE_ROLES: frozenset[Role] = frozenset({Role.CLIENT})


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
    """Protege el autorregistro. Solo se puede pedir un rol de esta lista."""
    if role not in SELF_ASSIGNABLE_ROLES:
        raise RoleNotSelfAssignable(role.value)


def ensure_role_is_allowed(role: Role, allowed: frozenset[Role]) -> None:
    """Decide si un rol alcanza para una operación.

    La regla vive en el dominio y no en el adaptador HTTP para que la misma
    comprobación sirva a un consumidor que no hable HTTP.
    """
    if role not in allowed:
        raise PermissionDenied(tuple(sorted(candidate.value for candidate in allowed)))

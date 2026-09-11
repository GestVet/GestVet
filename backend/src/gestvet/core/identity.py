"""Identidad compartida por todos los módulos.

Quién es el usuario y qué rol tiene es una pregunta que se hace cada módulo:
mascotas, horarios y citas por igual. Si la respuesta viviera en `accounts`,
todos tendrían que importarlo y dejaría de haber módulos independientes.

Por eso el núcleo posee la *autenticación* (quién sos) y `accounts` posee la
*gestión de usuarios* (tu perfil, tu alta, el padrón). Este archivo es Python
puro a propósito: lo importa hasta la capa de dominio.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


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

# El personal de la clínica: todo el que no es cliente y atiende el servicio.
STAFF_ROLES: frozenset[Role] = frozenset(
    {Role.ADMIN, Role.VETERINARIAN, Role.EMERGENCY_VETERINARIAN}
)
# Roles que atienden citas.
VETERINARIAN_ROLES: frozenset[Role] = frozenset({Role.VETERINARIAN, Role.EMERGENCY_VETERINARIAN})


@dataclass(frozen=True, slots=True)
class Principal:
    """Quien hace la petición, reducido a lo que la autorización necesita.

    No es la entidad `User` de `accounts`: no trae nombre ni teléfono. Un
    módulo que solo tiene que decidir si puede tocar un recurso no necesita
    conocer el perfil de nadie.
    """

    user_id: int
    role: Role
    is_active: bool


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str
    expires_in_seconds: int


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: int
    role: Role


class TokenService(Protocol):
    """Puerto de emisión y lectura de credenciales portables.

    Qué formato tengan (JWT, PASETO, una fila en Redis) es decisión del
    adaptador. El negocio solo necesita ir de una identidad a un token y volver.
    """

    def issue(self, user_id: int, role: Role) -> AccessToken: ...

    def decode(self, token: str) -> TokenClaims: ...


class IdentityError(Exception):
    """Raíz de los errores de identidad."""


class InvalidToken(IdentityError):
    def __init__(self, reason: str = "El token no es válido o ya expiró.") -> None:
        super().__init__(reason)
        self.reason = reason


class PermissionDenied(IdentityError):
    def __init__(self, required: tuple[str, ...]) -> None:
        super().__init__(f"Se requiere uno de estos roles: {', '.join(required)}.")
        self.required = required


def ensure_role_is_allowed(role: Role, allowed: frozenset[Role]) -> None:
    """Decide si un rol alcanza para una operación.

    Vive acá y no en el adaptador HTTP para que la misma comprobación sirva a
    un consumidor que no hable HTTP.
    """
    if role not in allowed:
        raise PermissionDenied(tuple(sorted(candidate.value for candidate in allowed)))

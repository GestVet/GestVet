"""Puerto de emisión y lectura de tokens de acceso.

El negocio necesita convertir una identidad en una credencial portable y de
vuelta. Qué formato tenga esa credencial (JWT, PASETO, una fila en Redis) es
una decisión del adaptador, no del caso de uso.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gestvet.accounts.domain.entities import Role


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str
    expires_in_seconds: int


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: int
    role: Role


class TokenService(Protocol):
    def issue(self, user_id: int, role: Role) -> AccessToken: ...

    def decode(self, token: str) -> TokenClaims: ...

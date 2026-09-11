"""Puerto de persistencia de cuentas.

Define *qué* necesita el negocio, nunca *cómo* se guarda. La implementación con
SQLAlchemy vive en `adapters/persistence` y esta capa no la conoce.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gestvet.accounts.domain.entities import User
from gestvet.core.identity import Role


@dataclass(frozen=True, slots=True)
class ClientQuery:
    """Criterios de búsqueda para el listado de clientes."""

    search: str | None = None
    is_active: bool | None = None
    ordering: str | None = None
    limit: int = 25
    offset: int = 0


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    total: int


class UserRepository(Protocol):
    async def add(self, user: User) -> User: ...

    async def get(self, user_id: int) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def exists_with_email(self, email: str) -> bool: ...

    async def search_by_role(self, role: Role, query: ClientQuery) -> Page[User]: ...


class PasswordHasher(Protocol):
    """Puerto de cifrado. El dominio nunca ve la librería concreta."""

    def hash(self, plain_password: str) -> str: ...

    def verify(self, plain_password: str, password_hash: str) -> bool: ...

    def dummy_hash(self) -> str:
        """Hash válido que ninguna contraseña reproduce.

        Lo pide el negocio, no la criptografía: al autenticar un correo que no
        existe hay que gastar el mismo tiempo que con uno real, o la latencia
        de la respuesta delata qué cuentas están registradas.
        """
        ...

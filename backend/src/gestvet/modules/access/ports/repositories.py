"""Puertos del módulo de accesos.

Los roles y sus asignaciones son datos propios. Qué tipo de cuenta tiene cada
persona lo posee `accounts`, así que se pregunta con un lector de solo lectura,
igual que el resto de los módulos hace con tablas ajenas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gestvet.core.identity import Role
from gestvet.modules.access.domain.entities import AccessRole


@dataclass(frozen=True, slots=True)
class AccountSummary:
    user_id: int
    account_kind: Role


class AccessRoleRepository(Protocol):
    async def list_all(self) -> list[AccessRole]: ...

    async def get(self, role_id: int) -> AccessRole | None: ...

    async def get_by_name(self, name: str) -> AccessRole | None: ...

    async def get_system(self, account_kind: Role) -> AccessRole | None: ...

    async def add(self, role: AccessRole) -> AccessRole: ...

    async def save(self, role: AccessRole) -> AccessRole: ...

    async def delete(self, role_id: int) -> None: ...


class RoleAssignments(Protocol):
    async def role_of(self, user_id: int) -> int | None: ...

    async def assign(self, user_id: int, role_id: int) -> None: ...

    async def clear(self, user_id: int) -> None: ...

    async def users_with_role(self, role_id: int) -> list[int]: ...

    async def all_assignments(self) -> dict[int, int]: ...


class AccountDirectory(Protocol):
    async def get(self, user_id: int) -> AccountSummary | None: ...

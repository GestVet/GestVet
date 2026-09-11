"""Caso de uso: consultar la bitácora enriquecida con quién hizo cada cosa.

El núcleo guarda solo el identificador de la cuenta, porque es lo único que
necesita para escribir. El nombre y el rol los posee este módulo, así que la
unión de las dos mitades ocurre acá.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityQuery, ActivityReader, ActivityRecord
from gestvet.core.identity import Role
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.accounts.ports.user_repository import UserQuery, UserRepository

# Cota para la resolución de nombres: la página de bitácora nunca trae más
# asientos que esto, así que tampoco más cuentas distintas.
MAX_USERS_PER_PAGE = 100


@dataclass(frozen=True, slots=True)
class ActivityEntry:
    record: ActivityRecord
    user: User


@dataclass(frozen=True, slots=True)
class ReadActivityQuery:
    roles: frozenset[Role] | None = None
    kinds: frozenset[ActivityKind] | None = None
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


class ReadActivity:
    def __init__(self, activity: ActivityReader, users: UserRepository) -> None:
        self._activity = activity
        self._users = users

    async def __call__(self, query: ReadActivityQuery) -> Page[ActivityEntry]:
        user_ids = await self._ids_for_roles(query.roles)
        if user_ids is not None and not user_ids:
            return Page(items=[], total=0)

        page = await self._activity.search(
            ActivityQuery(
                user_ids=user_ids,
                kinds=query.kinds,
                limit=query.limit,
                offset=query.offset,
            )
        )
        autores = await self._users_by_id({record.user_id for record in page.items})

        return Page(
            items=[
                ActivityEntry(record=record, user=autores[record.user_id])
                for record in page.items
                if record.user_id in autores
            ],
            total=page.total,
        )

    async def _ids_for_roles(self, roles: frozenset[Role] | None) -> frozenset[int] | None:
        """Traduce un filtro por rol a un conjunto de cuentas.

        El núcleo no conoce los roles, así que el recorte se resuelve acá y
        viaja como una lista de identificadores.
        """
        if roles is None:
            return None
        page = await self._users.search(UserQuery(roles=roles, limit=MAX_USERS_PER_PAGE))
        return frozenset(user.id for user in page.items if user.id is not None)

    async def _users_by_id(self, ids: set[int]) -> dict[int, User]:
        if not ids:
            return {}
        page = await self._users.search(UserQuery(ids=frozenset(ids), limit=MAX_USERS_PER_PAGE))
        return {user.id: user for user in page.items if user.id is not None}

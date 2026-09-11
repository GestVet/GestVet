"""Caso de uso: listado paginado de clientes."""

from __future__ import annotations

from gestvet.accounts.domain.entities import Role, User
from gestvet.accounts.ports.user_repository import ClientQuery, UserRepository
from gestvet.core.pagination import Page

# Sólo estas columnas pueden ordenar el listado. Un valor desconocido cae al
# predeterminado en lugar de viajar hacia la base de datos.
ORDERABLE_FIELDS = frozenset({"email", "first_name", "last_name", "created_at", "is_active"})
DEFAULT_ORDERING = "last_name"


def resolve_ordering(ordering: str | None) -> str:
    if not ordering:
        return DEFAULT_ORDERING
    field = ordering.removeprefix("-")
    return ordering if field in ORDERABLE_FIELDS else DEFAULT_ORDERING


class ListClients:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def __call__(self, query: ClientQuery) -> Page[User]:
        safe_query = ClientQuery(
            search=query.search,
            is_active=query.is_active,
            ordering=resolve_ordering(query.ordering),
            limit=query.limit,
            offset=query.offset,
        )
        return await self._users.search_by_role(Role.CLIENT, safe_query)

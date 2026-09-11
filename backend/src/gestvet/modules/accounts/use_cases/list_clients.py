"""Caso de uso: listado paginado de clientes."""

from __future__ import annotations

from gestvet.core.identity import Role
from gestvet.core.pagination import Page
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.accounts.ports.user_repository import UserQuery, UserRepository

# Sólo estas columnas pueden ordenar el listado. Un valor desconocido cae al
# predeterminado en lugar de viajar hacia la base de datos.
ORDERABLE_FIELDS = frozenset({"email", "first_name", "last_name", "created_at", "is_active"})
DEFAULT_ORDERING = "last_name"


def resolve_ordering(ordering: str | None) -> str:
    if not ordering:
        return DEFAULT_ORDERING
    field = ordering.removeprefix("-")
    return ordering if field in ORDERABLE_FIELDS else DEFAULT_ORDERING


class ListUsers:
    """Listado del padrón acotado a un conjunto de roles.

    El recorte se decide acá y no en el adaptador HTTP: un listado que sirve
    datos personales no puede depender de que el endpoint se acuerde de pasar
    el filtro correcto.
    """

    def __init__(self, users: UserRepository, roles: frozenset[Role]) -> None:
        self._users = users
        self._roles = roles

    async def __call__(self, query: UserQuery) -> Page[User]:
        return await self._users.search(
            UserQuery(
                roles=self._roles,
                search=query.search,
                is_active=query.is_active,
                ordering=resolve_ordering(query.ordering),
                limit=query.limit,
                offset=query.offset,
            )
        )


# Conjuntos con nombre, para que ningún endpoint arme el recorte a mano.
CLIENT_ROLES: frozenset[Role] = frozenset({Role.CLIENT})
STAFF_LISTING_ROLES: frozenset[Role] = frozenset({Role.VETERINARIAN, Role.EMERGENCY_VETERINARIAN})

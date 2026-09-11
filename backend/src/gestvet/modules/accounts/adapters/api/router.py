"""Adaptador de entrada HTTP para la gestión de clientes.

Traduce peticiones a comandos y errores de dominio a códigos de estado. No
contiene reglas de negocio ni consultas.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from gestvet.core.auth import require_roles
from gestvet.core.identity import STAFF_ROLES
from gestvet.modules.accounts.adapters.api.dependencies import UserRepositoryDep
from gestvet.modules.accounts.adapters.api.schemas import ClientPageResponse, UserResponse
from gestvet.modules.accounts.ports.user_repository import UserQuery
from gestvet.modules.accounts.use_cases.list_clients import CLIENT_ROLES, ListUsers

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# El padrón de clientes es dato personal. Solo lo ve quien atiende la clínica,
# nunca un cliente autenticado mirando el listado de los demás.
router = APIRouter(dependencies=[Depends(require_roles(*STAFF_ROLES))])


@router.get("", response_model=ClientPageResponse, summary="Listar clientes")
async def list_clients(
    users: UserRepositoryDep,
    search: Annotated[str | None, Query(description="Busca en nombre, correo y teléfono")] = None,
    ordering: Annotated[str | None, Query(description="Columna, '-' invierte")] = None,
    is_active: Annotated[bool | None, Query(description="Filtra por estado")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ClientPageResponse:
    page = await ListUsers(users, CLIENT_ROLES)(
        UserQuery(
            search=search,
            is_active=is_active,
            ordering=ordering,
            limit=limit,
            offset=offset,
        )
    )
    return ClientPageResponse(
        items=[UserResponse.from_entity(user) for user in page.items],
        total=page.total,
    )

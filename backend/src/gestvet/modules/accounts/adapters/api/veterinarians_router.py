"""Listado de veterinarios para quien va a reservar.

Cualquier cuenta autenticada puede verlo, pero solo con lo que hace falta para
elegir: identificador, nombre y rol. El padrón completo del personal, con sus
datos de contacto, sigue siendo cosa de la administración.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from gestvet.core.auth import get_principal
from gestvet.core.pagination import MAX_PAGE_SIZE
from gestvet.modules.accounts.adapters.api.dependencies import UserRepositoryDep
from gestvet.modules.accounts.adapters.api.schemas import (
    VeterinarianListResponse,
    VeterinarianResponse,
)
from gestvet.modules.accounts.ports.user_repository import UserQuery
from gestvet.modules.accounts.use_cases.list_clients import STAFF_LISTING_ROLES, ListUsers

router = APIRouter(dependencies=[Depends(get_principal)])


@router.get("", response_model=VeterinarianListResponse, summary="Veterinarios que atienden")
async def list_veterinarians(users: UserRepositoryDep) -> VeterinarianListResponse:
    page = await ListUsers(users, STAFF_LISTING_ROLES)(
        UserQuery(is_active=True, limit=MAX_PAGE_SIZE)
    )
    return VeterinarianListResponse(
        items=[VeterinarianResponse.from_entity(user) for user in page.items],
        total=page.total,
    )

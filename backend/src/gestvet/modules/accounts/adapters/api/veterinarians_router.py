"""Listado de veterinarios para quien va a reservar.

Cualquier cuenta autenticada puede verlo, pero solo con lo que hace falta para
elegir: identificador, nombre, rol y qué tan bien lo calificaron quienes ya
lo tuvieron. El padrón completo del personal, con sus datos de contacto,
sigue siendo cosa de la administración.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from gestvet.core.auth import require_permission
from gestvet.core.pagination import MAX_PAGE_SIZE
from gestvet.core.permissions import Permission
from gestvet.modules.accounts.adapters.api.dependencies import (
    ReviewsDirectoryDep,
    SpecialtyRepositoryDep,
    UserRepositoryDep,
)
from gestvet.modules.accounts.adapters.api.schemas import (
    VeterinarianListResponse,
    VeterinarianResponse,
)
from gestvet.modules.accounts.ports.reviews_directory import RatingSummary
from gestvet.modules.accounts.ports.user_repository import UserQuery
from gestvet.modules.accounts.use_cases.list_clients import BOOKABLE_VETERINARIAN_ROLES, ListUsers

router = APIRouter(dependencies=[Depends(require_permission(Permission.VETERINARIANS_READ))])


@router.get("", response_model=VeterinarianListResponse, summary="Veterinarios que atienden")
async def list_veterinarians(
    users: UserRepositoryDep, reviews: ReviewsDirectoryDep, specialties: SpecialtyRepositoryDep
) -> VeterinarianListResponse:
    # El de guardia no aparece acá: HU09 lo reserva para el reparto automático
    # de emergencias, no para que un cliente lo elija a mano.
    page = await ListUsers(users, BOOKABLE_VETERINARIAN_ROLES)(
        UserQuery(is_active=True, limit=MAX_PAGE_SIZE)
    )
    ids = [user.id for user in page.items if user.id]
    summaries = await reviews.summaries_for(ids)
    by_user = await specialties.specialties_for(frozenset(ids))
    vacio = RatingSummary(average=None, count=0)
    return VeterinarianListResponse(
        items=[
            VeterinarianResponse.from_entity(
                user,
                summaries.get(user.id or 0, vacio).average,
                summaries.get(user.id or 0, vacio).count,
                by_user.get(user.id or 0, []),
            )
            for user in page.items
        ],
        total=page.total,
    )

"""Adaptador de entrada HTTP del panorama de mascotas.

Router aparte del resto de indicadores porque el permiso es distinto: acá
también entra el veterinario (recortado a lo que atendió), y el resto del
panel de indicadores es solo para administración.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from gestvet.core.auth import require_permission
from gestvet.core.clinic_time import clinic_date
from gestvet.core.identity import Principal, Role
from gestvet.core.permissions import Permission
from gestvet.modules.insights.adapters.api.dependencies import PetOverviewDirectoryDep
from gestvet.modules.insights.adapters.api.schemas import (
    PetOverviewListResponse,
    PetOverviewResponse,
)
from gestvet.modules.insights.use_cases.list_pet_overview import ListPetOverview

router = APIRouter()

ViewerDep = Annotated[Principal, Depends(require_permission(Permission.PETS_OVERVIEW_READ))]


@router.get(
    "/pets-overview",
    response_model=PetOverviewListResponse,
    summary="Panorama de mascotas: administración ve todas, veterinario solo las que atendió",
)
async def list_pet_overview(
    viewer: ViewerDep, directory: PetOverviewDirectoryDep
) -> PetOverviewListResponse:
    veterinarian_id = None if viewer.role is Role.ADMIN else viewer.user_id
    items = await ListPetOverview(directory)(veterinarian_id, clinic_date(datetime.now(UTC)))
    return PetOverviewListResponse(items=[PetOverviewResponse.from_entity(item) for item in items])

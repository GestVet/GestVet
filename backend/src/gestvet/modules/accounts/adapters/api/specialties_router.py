"""Catálogo de especialidades veterinarias.

Cualquier cuenta autenticada lo lee: lo necesita el cliente para filtrar al
reservar y la administración para asignarlo al dar de alta un veterinario.
Agregar y corregir una especialidad es cosa de la administración.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from gestvet.core.auth import get_principal, require_permission
from gestvet.core.identity import Principal
from gestvet.core.permissions import Permission
from gestvet.modules.accounts.adapters.api.dependencies import SpecialtyRepositoryDep
from gestvet.modules.accounts.adapters.api.schemas import (
    AddSpecialtyRequest,
    SpecialtyListResponse,
    SpecialtyResponse,
    UpdateSpecialtyRequest,
)
from gestvet.modules.accounts.domain.exceptions import (
    AccountsError,
    SpecialtyNameTaken,
    SpecialtyNotFound,
)
from gestvet.modules.accounts.use_cases.manage_specialties import (
    AddSpecialty,
    AddSpecialtyCommand,
    UpdateSpecialty,
    UpdateSpecialtyCommand,
)

router = APIRouter()

CatalogManagerDep = Annotated[
    Principal, Depends(require_permission(Permission.SPECIALTIES_MANAGE_CATALOG))
]


def _to_http(error: AccountsError) -> HTTPException:
    if isinstance(error, SpecialtyNotFound):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(error))
    if isinstance(error, SpecialtyNameTaken):
        return HTTPException(status.HTTP_409_CONFLICT, str(error))
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error))


@router.get(
    "",
    response_model=SpecialtyListResponse,
    dependencies=[Depends(get_principal)],
    summary="Especialidades que se ofrecen",
)
async def list_specialties(catalog: SpecialtyRepositoryDep) -> SpecialtyListResponse:
    items = await catalog.list_all(include_inactive=False)
    return SpecialtyListResponse(items=[SpecialtyResponse.from_entity(item) for item in items])


@router.get(
    "/manage",
    response_model=SpecialtyListResponse,
    dependencies=[Depends(require_permission(Permission.SPECIALTIES_MANAGE_CATALOG))],
    summary="El catálogo completo, con lo desactivado",
)
async def list_managed_specialties(catalog: SpecialtyRepositoryDep) -> SpecialtyListResponse:
    items = await catalog.list_all(include_inactive=True)
    return SpecialtyListResponse(items=[SpecialtyResponse.from_entity(item) for item in items])


@router.post(
    "",
    response_model=SpecialtyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar una especialidad",
)
async def add_specialty(
    payload: AddSpecialtyRequest,
    manager: CatalogManagerDep,
    catalog: SpecialtyRepositoryDep,
) -> SpecialtyResponse:
    try:
        specialty = await AddSpecialty(catalog)(
            AddSpecialtyCommand(
                name=payload.name, category=payload.category, description=payload.description
            )
        )
    except AccountsError as error:
        raise _to_http(error) from error
    return SpecialtyResponse.from_entity(specialty)


@router.patch(
    "/{specialty_id}",
    response_model=SpecialtyResponse,
    summary="Corregir, activar o desactivar una especialidad",
)
async def update_specialty(
    specialty_id: int,
    payload: UpdateSpecialtyRequest,
    manager: CatalogManagerDep,
    catalog: SpecialtyRepositoryDep,
) -> SpecialtyResponse:
    try:
        specialty = await UpdateSpecialty(catalog)(
            UpdateSpecialtyCommand(
                specialty_id=specialty_id,
                name=payload.name,
                category=payload.category,
                description=payload.description,
                is_active=payload.is_active,
            )
        )
    except AccountsError as error:
        raise _to_http(error) from error
    return SpecialtyResponse.from_entity(specialty)

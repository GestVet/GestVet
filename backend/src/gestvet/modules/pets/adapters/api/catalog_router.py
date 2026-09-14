"""Adaptador de entrada HTTP para el catálogo de especies y razas.

Cualquier cuenta lee lo que se ofrece hoy, porque lo necesita para registrar o
editar una mascota. Agregar y corregir exige administrar el catálogo, y cada
cambio avisa en tiempo real para que los formularios abiertos lo reciban.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from gestvet.core.auth import get_principal, require_permission
from gestvet.core.identity import Principal, Role
from gestvet.core.permissions import Permission
from gestvet.core.realtime import PET_CATALOG_TOPIC, RealtimeEvent
from gestvet.core.realtime_broker import EventPublisherDep
from gestvet.modules.pets.adapters.api.catalog_schemas import (
    CatalogBreedResponse,
    CatalogNameRequest,
    CatalogSpeciesResponse,
    ManagedCatalogResponse,
    PetCatalogResponse,
    UpdateCatalogEntryRequest,
)
from gestvet.modules.pets.adapters.api.dependencies import PetCatalogRepositoryDep
from gestvet.modules.pets.domain.exceptions import (
    CatalogEntryLocked,
    CatalogEntryNotFound,
    CatalogNameTaken,
    InvalidPetData,
    PetsError,
)
from gestvet.modules.pets.use_cases.manage_catalog import (
    AddBreed,
    AddBreedCommand,
    AddSpecies,
    UpdateBreed,
    UpdateCatalogEntryCommand,
    UpdateSpecies,
)

router = APIRouter()

CatalogManagerDep = Annotated[
    Principal, Depends(require_permission(Permission.PETS_MANAGE_CATALOG))
]

_STATUS_BY_ERROR: tuple[tuple[type[PetsError], int], ...] = (
    (CatalogEntryNotFound, status.HTTP_404_NOT_FOUND),
    (CatalogNameTaken, status.HTTP_409_CONFLICT),
    (CatalogEntryLocked, status.HTTP_409_CONFLICT),
    (InvalidPetData, status.HTTP_422_UNPROCESSABLE_CONTENT),
)


def _to_http(error: PetsError) -> HTTPException:
    for error_type, code in _STATUS_BY_ERROR:
        if isinstance(error, error_type):
            return HTTPException(code, str(error))
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(error))


def _notify_change(events: EventPublisherDep) -> None:
    # Todas las cuentas usan el catálogo en algún formulario.
    events.publish(RealtimeEvent(topic=PET_CATALOG_TOPIC, roles=frozenset(Role)))


@router.get(
    "",
    response_model=PetCatalogResponse,
    dependencies=[Depends(get_principal)],
    summary="Especies y razas que se ofrecen",
)
async def read_pet_catalog(catalog: PetCatalogRepositoryDep) -> PetCatalogResponse:
    return PetCatalogResponse.from_entities(await catalog.list_species(include_inactive=False))


@router.get(
    "/manage",
    response_model=ManagedCatalogResponse,
    dependencies=[Depends(require_permission(Permission.PETS_MANAGE_CATALOG))],
    summary="El catálogo completo, con lo desactivado",
)
async def read_managed_catalog(catalog: PetCatalogRepositoryDep) -> ManagedCatalogResponse:
    species = await catalog.list_species(include_inactive=True)
    return ManagedCatalogResponse(
        species=[CatalogSpeciesResponse.from_entity(item) for item in species]
    )


@router.post(
    "/species",
    response_model=CatalogSpeciesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar una especie",
)
async def add_species(
    payload: CatalogNameRequest,
    manager: CatalogManagerDep,
    catalog: PetCatalogRepositoryDep,
    events: EventPublisherDep,
) -> CatalogSpeciesResponse:
    try:
        species = await AddSpecies(catalog)(payload.name)
    except PetsError as error:
        raise _to_http(error) from error
    _notify_change(events)
    return CatalogSpeciesResponse.from_entity(species)


@router.patch(
    "/species/{species_id}",
    response_model=CatalogSpeciesResponse,
    summary="Corregir, activar o desactivar una especie",
)
async def update_species(
    species_id: int,
    payload: UpdateCatalogEntryRequest,
    manager: CatalogManagerDep,
    catalog: PetCatalogRepositoryDep,
    events: EventPublisherDep,
) -> CatalogSpeciesResponse:
    try:
        species = await UpdateSpecies(catalog)(
            UpdateCatalogEntryCommand(
                entry_id=species_id, name=payload.name, is_active=payload.is_active
            )
        )
    except PetsError as error:
        raise _to_http(error) from error
    _notify_change(events)
    return CatalogSpeciesResponse.from_entity(species)


@router.post(
    "/species/{species_id}/breeds",
    response_model=CatalogBreedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar una raza a una especie",
)
async def add_breed(
    species_id: int,
    payload: CatalogNameRequest,
    manager: CatalogManagerDep,
    catalog: PetCatalogRepositoryDep,
    events: EventPublisherDep,
) -> CatalogBreedResponse:
    try:
        breed = await AddBreed(catalog)(AddBreedCommand(species_id=species_id, name=payload.name))
    except PetsError as error:
        raise _to_http(error) from error
    _notify_change(events)
    return CatalogBreedResponse.from_entity(breed)


@router.patch(
    "/breeds/{breed_id}",
    response_model=CatalogBreedResponse,
    summary="Corregir, activar o desactivar una raza",
)
async def update_breed(
    breed_id: int,
    payload: UpdateCatalogEntryRequest,
    manager: CatalogManagerDep,
    catalog: PetCatalogRepositoryDep,
    events: EventPublisherDep,
) -> CatalogBreedResponse:
    try:
        breed = await UpdateBreed(catalog)(
            UpdateCatalogEntryCommand(
                entry_id=breed_id, name=payload.name, is_active=payload.is_active
            )
        )
    except PetsError as error:
        raise _to_http(error) from error
    _notify_change(events)
    return CatalogBreedResponse.from_entity(breed)

"""Adaptador de entrada HTTP para mascotas.

Un cliente administra las suyas y solo las suyas. El personal de la clínica
puede consultarlas porque las necesita para atender una cita, pero no las da de
alta ni las modifica.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.auth import require_roles
from gestvet.core.identity import STAFF_ROLES, Principal, Role
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.modules.pets.adapters.api.dependencies import PetRepositoryDep
from gestvet.modules.pets.adapters.api.schemas import (
    ChangePetStatusRequest,
    PetPageResponse,
    PetResponse,
    RegisterPetRequest,
)
from gestvet.modules.pets.domain.exceptions import InvalidPetData, PetNotFound
from gestvet.modules.pets.ports.pet_repository import PetQuery
from gestvet.modules.pets.use_cases.change_pet_status import ChangePetStatus, ChangePetStatusCommand
from gestvet.modules.pets.use_cases.list_pets import ListPets
from gestvet.modules.pets.use_cases.register_pet import RegisterPet, RegisterPetCommand

router = APIRouter()

ClientDep = Annotated[Principal, Depends(require_roles(Role.CLIENT))]
StaffDep = Annotated[Principal, Depends(require_roles(*STAFF_ROLES))]


@router.post(
    "",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una mascota propia",
)
async def register_pet(
    payload: RegisterPetRequest,
    client: ClientDep,
    pets: PetRepositoryDep,
) -> PetResponse:
    try:
        pet = await RegisterPet(pets)(
            RegisterPetCommand(
                name=payload.name,
                species=payload.species,
                breed=payload.breed,
                birth_date=payload.birth_date,
                owner_id=client.user_id,
            )
        )
    except InvalidPetData as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return PetResponse.from_entity(pet)


@router.get("/mine", response_model=PetPageResponse, summary="Listar mis mascotas")
async def list_my_pets(
    client: ClientDep,
    pets: PetRepositoryDep,
    is_active: Annotated[bool | None, Query(description="Filtra por estado")] = None,
    search: Annotated[str | None, Query(description="Busca en nombre, especie y raza")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PetPageResponse:
    page = await ListPets(pets)(
        PetQuery(
            owner_id=client.user_id,
            is_active=is_active,
            search=search,
            limit=limit,
            offset=offset,
        )
    )
    return PetPageResponse(
        items=[PetResponse.from_entity(pet) for pet in page.items],
        total=page.total,
    )


@router.get("", response_model=PetPageResponse, summary="Listar mascotas de un cliente")
async def list_pets_of_owner(
    staff: StaffDep,
    pets: PetRepositoryDep,
    owner_id: Annotated[int, Query(ge=1, description="Cliente dueño de las mascotas")],
    is_active: Annotated[bool | None, Query(description="Filtra por estado")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PetPageResponse:
    page = await ListPets(pets)(
        PetQuery(owner_id=owner_id, is_active=is_active, limit=limit, offset=offset)
    )
    return PetPageResponse(
        items=[PetResponse.from_entity(pet) for pet in page.items],
        total=page.total,
    )


@router.patch(
    "/{pet_id}/status",
    response_model=PetResponse,
    summary="Dar de baja o reactivar una mascota propia",
)
async def change_pet_status(
    pet_id: int,
    payload: ChangePetStatusRequest,
    client: ClientDep,
    pets: PetRepositoryDep,
) -> PetResponse:
    try:
        pet = await ChangePetStatus(pets)(
            ChangePetStatusCommand(
                pet_id=pet_id, owner_id=client.user_id, is_active=payload.is_active
            )
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return PetResponse.from_entity(pet)

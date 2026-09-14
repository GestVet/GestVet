"""Adaptador de entrada HTTP para mascotas.

Un cliente administra las suyas y solo las suyas: el alta, la baja y los datos
que conoce de memoria (sexo, color, microchip, temperamento). El personal de
la clínica las consulta para atender una cita, y un veterinario además carga
los datos clínicos (peso, altura, esterilización, alergias) de cualquier
mascota: son datos que se confirman en consulta, no en el padrón del dueño.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.core.permissions import Permission
from gestvet.modules.pets.adapters.api.dependencies import (
    PetCatalogRepositoryDep,
    PetRepositoryDep,
)
from gestvet.modules.pets.adapters.api.schemas import (
    ChangePetStatusRequest,
    CorrectPetStatusRequest,
    PetPageResponse,
    PetResponse,
    RegisterPetForOwnerRequest,
    RegisterPetRequest,
    UpdatePetClinicalProfileRequest,
    UpdatePetOwnerProfileRequest,
)
from gestvet.modules.pets.domain.catalog import UNKNOWN_BREED
from gestvet.modules.pets.domain.exceptions import InvalidPetData, PetNotFound, PetStatusIsFinal
from gestvet.modules.pets.ports.pet_repository import PetQuery
from gestvet.modules.pets.use_cases.change_pet_status import ChangePetStatus, ChangePetStatusCommand
from gestvet.modules.pets.use_cases.correct_pet_status import (
    CorrectPetStatus,
    CorrectPetStatusCommand,
)
from gestvet.modules.pets.use_cases.list_pets import ListPets
from gestvet.modules.pets.use_cases.register_pet import RegisterPet, RegisterPetCommand
from gestvet.modules.pets.use_cases.update_pet_clinical_profile import (
    UpdatePetClinicalProfile,
    UpdatePetClinicalProfileCommand,
)
from gestvet.modules.pets.use_cases.update_pet_owner_profile import (
    UpdatePetOwnerProfile,
    UpdatePetOwnerProfileCommand,
)

router = APIRouter()

OwnerDep = Annotated[Principal, Depends(require_permission(Permission.PETS_MANAGE_OWN))]
PetRegistrarDep = Annotated[
    Principal, Depends(require_permission(Permission.PETS_REGISTER_FOR_OWNER))
]
PetsReaderDep = Annotated[Principal, Depends(require_permission(Permission.PETS_READ_ANY))]
PetStatusCorrectorDep = Annotated[
    Principal, Depends(require_permission(Permission.PETS_CORRECT_STATUS))
]
ClinicalProfileEditorDep = Annotated[
    Principal, Depends(require_permission(Permission.PETS_EDIT_CLINICAL_PROFILE))
]


@router.post(
    "",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una mascota propia",
)
async def register_pet(
    payload: RegisterPetRequest,
    client: OwnerDep,
    pets: PetRepositoryDep,
    catalog: PetCatalogRepositoryDep,
    activity: ActivityRecorderDep,
) -> PetResponse:
    try:
        pet = await RegisterPet(pets, catalog, activity)(
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


@router.post(
    "/for-owner",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una mascota a nombre de un cliente (alta exprés)",
)
async def register_pet_for_owner(
    payload: RegisterPetForOwnerRequest,
    staff: PetRegistrarDep,
    pets: PetRepositoryDep,
    catalog: PetCatalogRepositoryDep,
    activity: ActivityRecorderDep,
) -> PetResponse:
    try:
        pet = await RegisterPet(pets, catalog, activity)(
            RegisterPetCommand(
                name=payload.name,
                species=payload.species,
                breed=UNKNOWN_BREED,
                birth_date=date.today(),
                owner_id=payload.owner_id,
            )
        )
    except InvalidPetData as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return PetResponse.from_entity(pet)


@router.get("/mine", response_model=PetPageResponse, summary="Listar mis mascotas")
async def list_my_pets(
    client: OwnerDep,
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
    staff: PetsReaderDep,
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
    client: OwnerDep,
    pets: PetRepositoryDep,
    activity: ActivityRecorderDep,
) -> PetResponse:
    try:
        pet = await ChangePetStatus(pets, activity)(
            ChangePetStatusCommand(
                pet_id=pet_id, owner_id=client.user_id, is_active=payload.is_active
            )
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except PetStatusIsFinal as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return PetResponse.from_entity(pet)


@router.patch(
    "/{pet_id}/correct-status",
    response_model=PetResponse,
    summary="Corregir el estado de una mascota (personal de la clínica)",
)
async def correct_pet_status(
    pet_id: int,
    payload: CorrectPetStatusRequest,
    staff: PetStatusCorrectorDep,
    pets: PetRepositoryDep,
    activity: ActivityRecorderDep,
) -> PetResponse:
    try:
        pet = await CorrectPetStatus(pets, activity)(
            CorrectPetStatusCommand(
                pet_id=pet_id,
                actor_id=staff.user_id,
                is_active=payload.is_active,
                reason=payload.reason,
            )
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidPetData as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return PetResponse.from_entity(pet)


@router.patch(
    "/{pet_id}/owner-profile",
    response_model=PetResponse,
    summary="Actualizar la ficha de una mascota propia",
)
async def update_pet_owner_profile(
    pet_id: int,
    payload: UpdatePetOwnerProfileRequest,
    client: OwnerDep,
    pets: PetRepositoryDep,
    catalog: PetCatalogRepositoryDep,
    activity: ActivityRecorderDep,
) -> PetResponse:
    try:
        pet = await UpdatePetOwnerProfile(pets, catalog, activity)(
            UpdatePetOwnerProfileCommand(
                pet_id=pet_id,
                owner_id=client.user_id,
                sex=payload.sex,
                color=payload.color,
                microchip_number=payload.microchip_number,
                temperament=payload.temperament,
                species=payload.species,
                breed=payload.breed,
                birth_date=payload.birth_date,
            )
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidPetData as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return PetResponse.from_entity(pet)


@router.patch(
    "/{pet_id}/clinical-profile",
    response_model=PetResponse,
    summary="Actualizar fecha de nacimiento, peso, altura, esterilización y alergias",
)
async def update_pet_clinical_profile(
    pet_id: int,
    payload: UpdatePetClinicalProfileRequest,
    veterinarian: ClinicalProfileEditorDep,
    pets: PetRepositoryDep,
    activity: ActivityRecorderDep,
) -> PetResponse:
    try:
        pet = await UpdatePetClinicalProfile(pets, activity)(
            UpdatePetClinicalProfileCommand(
                pet_id=pet_id,
                updated_by=veterinarian.user_id,
                birth_date=payload.birth_date,
                weight_kg=payload.weight_kg,
                height_cm=payload.height_cm,
                is_sterilized=payload.is_sterilized,
                allergies=payload.allergies,
            )
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidPetData as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return PetResponse.from_entity(pet)

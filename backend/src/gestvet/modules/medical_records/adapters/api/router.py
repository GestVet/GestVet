"""Adaptador de entrada HTTP para la historia clínica.

Cargar una entrada es un acto clínico: solo un veterinario, de guardia o no,
llega hasta ahí. Leerla la puede pedir cualquier cuenta autenticada, pero un
cliente solo ve la de sus propias mascotas; el caso de uso aplica ese recorte.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import PrincipalDep, require_roles
from gestvet.core.identity import STAFF_ROLES, VETERINARIAN_ROLES, Principal
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.modules.medical_records.adapters.api.dependencies import (
    ClinicalEntryRepositoryDep,
    PetDirectoryDep,
)
from gestvet.modules.medical_records.adapters.api.schemas import (
    AddClinicalEntryRequest,
    ClinicalEntryPageResponse,
    ClinicalEntryResponse,
)
from gestvet.modules.medical_records.domain.entities import EntryKind
from gestvet.modules.medical_records.domain.exceptions import InvalidClinicalEntry, PetNotFound
from gestvet.modules.medical_records.ports.clinical_entry_repository import ClinicalEntryQuery
from gestvet.modules.medical_records.use_cases.add_clinical_entry import (
    AddClinicalEntry,
    AddClinicalEntryCommand,
)
from gestvet.modules.medical_records.use_cases.list_clinical_entries import ListClinicalEntries

router = APIRouter()

VeterinarianDep = Annotated[Principal, Depends(require_roles(*VETERINARIAN_ROLES))]


@router.post(
    "",
    response_model=ClinicalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar una entrada a la historia clínica",
)
async def add_clinical_entry(
    payload: AddClinicalEntryRequest,
    veterinarian: VeterinarianDep,
    entries: ClinicalEntryRepositoryDep,
    pets: PetDirectoryDep,
    activity: ActivityRecorderDep,
) -> ClinicalEntryResponse:
    try:
        entry = await AddClinicalEntry(entries, pets, activity)(
            AddClinicalEntryCommand(
                pet_id=payload.pet_id,
                veterinarian_id=veterinarian.user_id,
                kind=payload.kind,
                notes=payload.notes,
                diagnosis=payload.diagnosis,
                treatment=payload.treatment,
                weight_kg=payload.weight_kg,
                appointment_id=payload.appointment_id,
                occurred_at=payload.occurred_at,
            )
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidClinicalEntry as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return ClinicalEntryResponse.from_entity(entry)


@router.get(
    "",
    response_model=ClinicalEntryPageResponse,
    summary="Historia clínica de una mascota",
)
async def list_clinical_entries(
    principal: PrincipalDep,
    entries: ClinicalEntryRepositoryDep,
    pets: PetDirectoryDep,
    pet_id: Annotated[int, Query(ge=1, description="Mascota consultada")],
    kind: Annotated[EntryKind | None, Query(description="Filtra por tipo")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ClinicalEntryPageResponse:
    try:
        page = await ListClinicalEntries(entries, pets)(
            ClinicalEntryQuery(pet_id=pet_id, kind=kind, limit=limit, offset=offset),
            requester_id=principal.user_id,
            is_staff=principal.role in STAFF_ROLES,
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return ClinicalEntryPageResponse(
        items=[ClinicalEntryResponse.from_entity(item) for item in page.items],
        total=page.total,
    )

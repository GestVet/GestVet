"""Adaptador de entrada HTTP para internaciones.

Abrir una internación, agregar notas de seguimiento y dar de alta son actos
clínicos: solo un veterinario, de guardia o no, llega hasta ahí. Leerla la
puede pedir cualquier cuenta autenticada, pero un cliente solo ve las de sus
propias mascotas; el caso de uso aplica ese recorte.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import STAFF_ROLES, Principal
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.core.permissions import Permission
from gestvet.modules.hospitalizations.adapters.api.dependencies import (
    AppointmentDirectoryDep,
    HospitalizationRepositoryDep,
    NoteRepositoryDep,
    PetDirectoryDep,
)
from gestvet.modules.hospitalizations.adapters.api.schemas import (
    AddNoteRequest,
    DischargeRequest,
    HospitalizationPageResponse,
    HospitalizationResponse,
    NoteResponse,
    OpenHospitalizationRequest,
)
from gestvet.modules.hospitalizations.domain.exceptions import (
    AppointmentNotFound,
    HospitalizationAlreadyDischarged,
    HospitalizationNotFound,
    PetNotFound,
)
from gestvet.modules.hospitalizations.ports.hospitalization_repository import (
    HospitalizationQuery,
)
from gestvet.modules.hospitalizations.use_cases.add_note import AddNote, AddNoteCommand
from gestvet.modules.hospitalizations.use_cases.discharge_hospitalization import (
    DischargeHospitalization,
    DischargeHospitalizationCommand,
)
from gestvet.modules.hospitalizations.use_cases.list_hospitalizations import ListHospitalizations
from gestvet.modules.hospitalizations.use_cases.open_hospitalization import (
    OpenHospitalization,
    OpenHospitalizationCommand,
)

router = APIRouter()

HospitalizationManagerDep = Annotated[
    Principal, Depends(require_permission(Permission.HOSPITALIZATIONS_MANAGE))
]
HospitalizationsReaderDep = Annotated[
    Principal, Depends(require_permission(Permission.HOSPITALIZATIONS_READ))
]


@router.post(
    "",
    response_model=HospitalizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir una internación a partir de una cita",
)
async def open_hospitalization(
    payload: OpenHospitalizationRequest,
    veterinarian: HospitalizationManagerDep,
    hospitalizations: HospitalizationRepositoryDep,
    appointments: AppointmentDirectoryDep,
    activity: ActivityRecorderDep,
) -> HospitalizationResponse:
    try:
        hospitalization = await OpenHospitalization(hospitalizations, appointments, activity)(
            OpenHospitalizationCommand(
                appointment_id=payload.appointment_id,
                opened_by=veterinarian.user_id,
                reason=payload.reason,
            )
        )
    except AppointmentNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return HospitalizationResponse.from_entity(hospitalization)


@router.get("", response_model=HospitalizationPageResponse, summary="Internaciones de una mascota")
async def list_hospitalizations(
    principal: HospitalizationsReaderDep,
    hospitalizations: HospitalizationRepositoryDep,
    notes: NoteRepositoryDep,
    pets: PetDirectoryDep,
    pet_id: Annotated[int, Query(ge=1, description="Mascota consultada")],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> HospitalizationPageResponse:
    try:
        page = await ListHospitalizations(hospitalizations, pets)(
            HospitalizationQuery(pet_id=pet_id, limit=limit, offset=offset),
            requester_id=principal.user_id,
            is_staff=principal.role in STAFF_ROLES,
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return HospitalizationPageResponse(
        items=[
            HospitalizationResponse.from_entity(
                item, await notes.list_for_hospitalization(item.id or 0)
            )
            for item in page.items
        ],
        total=page.total,
    )


@router.post(
    "/{hospitalization_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar una nota de seguimiento a una internación abierta",
)
async def add_note(
    hospitalization_id: int,
    payload: AddNoteRequest,
    veterinarian: HospitalizationManagerDep,
    notes: NoteRepositoryDep,
    hospitalizations: HospitalizationRepositoryDep,
    activity: ActivityRecorderDep,
) -> NoteResponse:
    try:
        note = await AddNote(notes, hospitalizations, activity)(
            AddNoteCommand(
                hospitalization_id=hospitalization_id,
                author_id=veterinarian.user_id,
                note=payload.note,
            )
        )
    except HospitalizationNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except HospitalizationAlreadyDischarged as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return NoteResponse.from_entity(note)


@router.post(
    "/{hospitalization_id}/discharge",
    response_model=HospitalizationResponse,
    summary="Dar de alta una internación",
)
async def discharge_hospitalization(
    hospitalization_id: int,
    payload: DischargeRequest,
    veterinarian: HospitalizationManagerDep,
    hospitalizations: HospitalizationRepositoryDep,
    notes: NoteRepositoryDep,
    activity: ActivityRecorderDep,
) -> HospitalizationResponse:
    try:
        hospitalization = await DischargeHospitalization(hospitalizations, activity)(
            DischargeHospitalizationCommand(
                hospitalization_id=hospitalization_id,
                actor_id=veterinarian.user_id,
                discharge_notes=payload.discharge_notes,
            )
        )
    except HospitalizationNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except HospitalizationAlreadyDischarged as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return HospitalizationResponse.from_entity(
        hospitalization, await notes.list_for_hospitalization(hospitalization_id)
    )

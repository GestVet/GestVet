"""Adaptador de entrada HTTP para las citas.

Traduce peticiones a comandos y errores de dominio a códigos de estado. Quién
puede hacer qué con una cita lo decide el caso de uso, no este archivo: acá
solo se exige estar autenticado con el rol correcto para llegar al endpoint.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import PrincipalDep, require_roles
from gestvet.core.identity import VETERINARIAN_ROLES, Principal, Role
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.modules.appointments.adapters.api.dependencies import (
    AppointmentRepositoryDep,
    AppointmentTypeRepositoryDep,
    PetDirectoryDep,
    ScheduleDirectoryDep,
)
from gestvet.modules.appointments.adapters.api.schemas import (
    AppointmentPageResponse,
    AppointmentResponse,
    AppointmentTypeListResponse,
    AppointmentTypeResponse,
    BookAppointmentRequest,
    CancelAppointmentRequest,
    OpenEmergencyRequest,
)
from gestvet.modules.appointments.domain.entities import AppointmentStatus
from gestvet.modules.appointments.domain.exceptions import (
    AppointmentNotFound,
    AppointmentTypeNotFound,
    IllegalStatusChange,
    InvalidAppointment,
    NoEmergencyVeterinarian,
    OutsideAvailability,
    OverlappingAppointment,
    PetNotOwned,
    VeterinarianUnavailable,
)
from gestvet.modules.appointments.ports.repositories import AppointmentQuery
from gestvet.modules.appointments.use_cases.book_appointment import (
    BookAppointment,
    BookAppointmentCommand,
)
from gestvet.modules.appointments.use_cases.change_status import (
    ChangeAppointmentStatus,
    ChangeStatusCommand,
)
from gestvet.modules.appointments.use_cases.list_appointments import ListAppointments, scope_to
from gestvet.modules.appointments.use_cases.open_emergency import (
    OpenEmergency,
    OpenEmergencyCommand,
)

router = APIRouter()

ClientDep = Annotated[Principal, Depends(require_roles(Role.CLIENT))]
VeterinarianDep = Annotated[Principal, Depends(require_roles(*VETERINARIAN_ROLES))]

_CONFLICT_ERRORS = (
    OutsideAvailability,
    OverlappingAppointment,
    NoEmergencyVeterinarian,
    VeterinarianUnavailable,
)


@router.get(
    "/types",
    response_model=AppointmentTypeListResponse,
    summary="Motivos de consulta reservables",
)
async def list_types(
    principal: PrincipalDep,
    types: AppointmentTypeRepositoryDep,
) -> AppointmentTypeListResponse:
    # La emergencia no aparece: no se reserva, se abre.
    items = [AppointmentTypeResponse.from_entity(item) for item in await types.list_active()]
    return AppointmentTypeListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reservar una cita",
)
async def book_appointment(
    payload: BookAppointmentRequest,
    client: ClientDep,
    appointments: AppointmentRepositoryDep,
    types: AppointmentTypeRepositoryDep,
    pets: PetDirectoryDep,
    schedule: ScheduleDirectoryDep,
    activity: ActivityRecorderDep,
) -> AppointmentResponse:
    use_case = BookAppointment(appointments, types, pets, schedule, activity)
    try:
        appointment = await use_case(
            BookAppointmentCommand(
                client_id=client.user_id,
                pet_id=payload.pet_id,
                veterinarian_id=payload.veterinarian_id,
                appointment_type_id=payload.appointment_type_id,
                scheduled_at=payload.scheduled_at,
                description=payload.description,
            )
        )
    except (AppointmentTypeNotFound, PetNotOwned) as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except _CONFLICT_ERRORS as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except InvalidAppointment as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return AppointmentResponse.from_entity(appointment)


@router.post(
    "/emergency",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir una emergencia ahora",
)
async def open_emergency(
    payload: OpenEmergencyRequest,
    client: ClientDep,
    appointments: AppointmentRepositoryDep,
    types: AppointmentTypeRepositoryDep,
    pets: PetDirectoryDep,
    schedule: ScheduleDirectoryDep,
    activity: ActivityRecorderDep,
) -> AppointmentResponse:
    use_case = OpenEmergency(appointments, types, pets, schedule, activity)
    try:
        appointment = await use_case(
            OpenEmergencyCommand(
                client_id=client.user_id,
                pet_id=payload.pet_id,
                description=payload.description,
            )
        )
    except (AppointmentTypeNotFound, PetNotOwned) as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except NoEmergencyVeterinarian as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return AppointmentResponse.from_entity(appointment)


@router.get("", response_model=AppointmentPageResponse, summary="Listar citas")
async def list_appointments(
    principal: PrincipalDep,
    appointments: AppointmentRepositoryDep,
    status_filter: Annotated[
        list[AppointmentStatus] | None, Query(alias="status", description="Filtra por estado")
    ] = None,
    is_emergency: Annotated[bool | None, Query(description="Solo emergencias")] = None,
    pet_id: Annotated[int | None, Query(ge=1)] = None,
    starts_after: Annotated[datetime | None, Query(description="Desde")] = None,
    ends_before: Annotated[datetime | None, Query(description="Hasta")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AppointmentPageResponse:
    # El criterio se recorta al alcance del rol antes de tocar la base. Un
    # filtro que llega del cliente nunca amplía el conjunto, solo lo estrecha.
    query = scope_to(
        principal,
        AppointmentQuery(
            statuses=frozenset(status_filter) if status_filter else None,
            is_emergency=is_emergency,
            pet_id=pet_id,
            starts_after=starts_after,
            ends_before=ends_before,
            limit=limit,
            offset=offset,
        ),
    )
    page = await ListAppointments(appointments)(query)
    return AppointmentPageResponse(
        items=[AppointmentResponse.from_entity(item) for item in page.items],
        total=page.total,
    )


async def _change_status(
    appointment_id: int,
    principal: Principal,
    appointments: AppointmentRepositoryDep,
    activity: ActivityRecorderDep,
    target: AppointmentStatus,
    reason: str = "",
) -> AppointmentResponse:
    try:
        appointment = await ChangeAppointmentStatus(appointments, activity)(
            ChangeStatusCommand(
                appointment_id=appointment_id,
                actor_id=principal.user_id,
                actor_role=principal.role,
                target=target,
                reason=reason,
            )
        )
    except AppointmentNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except IllegalStatusChange as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except InvalidAppointment as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return AppointmentResponse.from_entity(appointment)


@router.post(
    "/{appointment_id}/confirm",
    response_model=AppointmentResponse,
    summary="Confirmar una cita",
)
async def confirm_appointment(
    appointment_id: int,
    veterinarian: VeterinarianDep,
    appointments: AppointmentRepositoryDep,
    activity: ActivityRecorderDep,
) -> AppointmentResponse:
    return await _change_status(
        appointment_id, veterinarian, appointments, activity, AppointmentStatus.CONFIRMED
    )


@router.post(
    "/{appointment_id}/complete",
    response_model=AppointmentResponse,
    summary="Dar por completada una cita",
)
async def complete_appointment(
    appointment_id: int,
    veterinarian: VeterinarianDep,
    appointments: AppointmentRepositoryDep,
    activity: ActivityRecorderDep,
) -> AppointmentResponse:
    return await _change_status(
        appointment_id, veterinarian, appointments, activity, AppointmentStatus.COMPLETED
    )


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    summary="Cancelar una cita",
)
async def cancel_appointment(
    appointment_id: int,
    payload: CancelAppointmentRequest,
    principal: PrincipalDep,
    appointments: AppointmentRepositoryDep,
    activity: ActivityRecorderDep,
) -> AppointmentResponse:
    # Cancelar lo pueden hacer las dos partes, así que acá basta con estar
    # autenticado: el caso de uso comprueba que participe en esa cita.
    return await _change_status(
        appointment_id,
        principal,
        appointments,
        activity,
        AppointmentStatus.CANCELLED,
        reason=payload.reason,
    )

"""Adaptador de entrada HTTP para las citas.

Traduce peticiones a comandos y errores de dominio a códigos de estado. Quién
puede hacer qué con una cita lo decide el caso de uso, no este archivo: acá
solo se exige estar autenticado con el permiso correcto para llegar al endpoint.

Cada cambio avisa en tiempo real al cliente, al veterinario de la cita y a la
administración. El aviso sale recién si la transacción se confirma. Confirmar
una cita, además, avisa al cliente por WhatsApp desde el caso de uso.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal, Role
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.core.permissions import Permission
from gestvet.core.realtime import APPOINTMENTS_TOPIC, EventPublisher, RealtimeEvent
from gestvet.core.realtime_broker import EventPublisherDep
from gestvet.modules.appointments.adapters.api.dependencies import (
    AppointmentLabelsDep,
    AppointmentRepositoryDep,
    AppointmentTypeRepositoryDep,
    ChangeStatusDep,
    PetDirectoryDep,
    RiskConsentDirectoryDep,
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
    OpenTimesResponse,
    OpenWalkInEmergencyRequest,
)
from gestvet.modules.appointments.domain.entities import Appointment, AppointmentStatus
from gestvet.modules.appointments.domain.exceptions import (
    AppointmentNotFound,
    AppointmentTypeNotFound,
    IllegalStatusChange,
    InvalidAppointment,
    NoEmergencyVeterinarian,
    OutsideAvailability,
    OverlappingAppointment,
    PetNotOwned,
    RiskConsentRejected,
    StatusChangeTooEarly,
    VeterinarianUnavailable,
)
from gestvet.modules.appointments.ports.appointment_labels import AppointmentLabelDirectory
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
from gestvet.modules.appointments.use_cases.list_open_times import (
    MAX_DAYS as MAX_OPEN_TIME_DAYS,
)
from gestvet.modules.appointments.use_cases.list_open_times import (
    ListOpenTimes,
    OpenTimesQuery,
    clinic_date,
)
from gestvet.modules.appointments.use_cases.open_emergency import (
    OpenEmergency,
    OpenEmergencyCommand,
)

router = APIRouter()

# Dos semanas: alcanza para planificar una consulta sin volver la tira de días
# inmanejable en un celular.
DEFAULT_OPEN_TIME_DAYS = 14

ReaderDep = Annotated[Principal, Depends(require_permission(Permission.APPOINTMENTS_READ))]
BookerDep = Annotated[Principal, Depends(require_permission(Permission.APPOINTMENTS_BOOK))]
EmergencyOpenerDep = Annotated[Principal, Depends(require_permission(Permission.EMERGENCIES_OPEN))]
WalkInDep = Annotated[Principal, Depends(require_permission(Permission.EMERGENCIES_OPEN_WALK_IN))]
AttendantDep = Annotated[Principal, Depends(require_permission(Permission.APPOINTMENTS_ATTEND))]
CancelerDep = Annotated[Principal, Depends(require_permission(Permission.APPOINTMENTS_CANCEL))]

_CONFLICT_ERRORS = (
    OutsideAvailability,
    OverlappingAppointment,
    NoEmergencyVeterinarian,
    VeterinarianUnavailable,
)


async def _notify_change(
    events: EventPublisher, appointment: Appointment, labels: AppointmentLabelDirectory
) -> AppointmentResponse:
    events.publish(
        RealtimeEvent(
            topic=APPOINTMENTS_TOPIC,
            user_ids=frozenset({appointment.client_id, appointment.veterinarian_id}),
            roles=frozenset({Role.ADMIN}),
            reference_id=appointment.id,
        )
    )
    found = await labels.labels_for([appointment.id or 0])
    return AppointmentResponse.from_entity(appointment, found.get(appointment.id or 0))


@router.get(
    "/types",
    response_model=AppointmentTypeListResponse,
    summary="Motivos de consulta reservables",
)
async def list_types(
    principal: ReaderDep,
    types: AppointmentTypeRepositoryDep,
) -> AppointmentTypeListResponse:
    # La emergencia no aparece: no se reserva, se abre.
    items = [AppointmentTypeResponse.from_entity(item) for item in await types.list_active()]
    return AppointmentTypeListResponse(items=items, total=len(items))


@router.get(
    "/open-times",
    response_model=OpenTimesResponse,
    summary="Horas libres para reservar, por día y veterinario",
)
async def list_open_times(
    principal: BookerDep,
    appointment_type_id: Annotated[int, Query(ge=1, description="Motivo: define la duración")],
    appointments: AppointmentRepositoryDep,
    types: AppointmentTypeRepositoryDep,
    schedule: ScheduleDirectoryDep,
    from_date: Annotated[
        date | None, Query(description="Primer día, en la fecha de la clínica. Por defecto, hoy")
    ] = None,
    days: Annotated[int, Query(ge=1, le=MAX_OPEN_TIME_DAYS)] = DEFAULT_OPEN_TIME_DAYS,
) -> OpenTimesResponse:
    now = datetime.now(UTC)
    try:
        found = await ListOpenTimes(appointments, types, schedule)(
            OpenTimesQuery(
                appointment_type_id=appointment_type_id,
                first_day=from_date or clinic_date(now),
                days=days,
                now=now,
            )
        )
    except AppointmentTypeNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidAppointment as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return OpenTimesResponse.from_days(found)


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reservar una cita",
)
async def book_appointment(
    payload: BookAppointmentRequest,
    client: BookerDep,
    appointments: AppointmentRepositoryDep,
    types: AppointmentTypeRepositoryDep,
    pets: PetDirectoryDep,
    schedule: ScheduleDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
    labels: AppointmentLabelsDep,
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
    return await _notify_change(events, appointment, labels)


@router.post(
    "/emergency",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir una emergencia ahora",
)
async def open_emergency(
    payload: OpenEmergencyRequest,
    client: EmergencyOpenerDep,
    appointments: AppointmentRepositoryDep,
    types: AppointmentTypeRepositoryDep,
    pets: PetDirectoryDep,
    schedule: ScheduleDirectoryDep,
    consents: RiskConsentDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
    labels: AppointmentLabelsDep,
) -> AppointmentResponse:
    use_case = OpenEmergency(appointments, types, pets, schedule, consents, activity)
    try:
        appointment = await use_case(
            OpenEmergencyCommand(
                client_id=client.user_id,
                pet_id=payload.pet_id,
                risk_consent_id=payload.risk_consent_id,
                description=payload.description,
            )
        )
    except (AppointmentTypeNotFound, PetNotOwned) as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except NoEmergencyVeterinarian as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except RiskConsentRejected as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return await _notify_change(events, appointment, labels)


@router.post(
    "/emergency/walk-in",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir una emergencia para un cliente dado de alta en el mostrador",
)
async def open_walk_in_emergency(
    payload: OpenWalkInEmergencyRequest,
    staff: WalkInDep,
    appointments: AppointmentRepositoryDep,
    types: AppointmentTypeRepositoryDep,
    pets: PetDirectoryDep,
    schedule: ScheduleDirectoryDep,
    consents: RiskConsentDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
    labels: AppointmentLabelsDep,
) -> AppointmentResponse:
    use_case = OpenEmergency(appointments, types, pets, schedule, consents, activity)
    try:
        appointment = await use_case(
            OpenEmergencyCommand(
                client_id=payload.client_id,
                pet_id=payload.pet_id,
                risk_consent_id=payload.risk_consent_id,
                description=payload.description,
            )
        )
    except (AppointmentTypeNotFound, PetNotOwned) as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except NoEmergencyVeterinarian as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except RiskConsentRejected as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return await _notify_change(events, appointment, labels)


@router.get("", response_model=AppointmentPageResponse, summary="Listar citas")
async def list_appointments(
    principal: ReaderDep,
    appointments: AppointmentRepositoryDep,
    labels: AppointmentLabelsDep,
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
    found = await labels.labels_for([item.id or 0 for item in page.items])
    return AppointmentPageResponse(
        items=[
            AppointmentResponse.from_entity(item, found.get(item.id or 0)) for item in page.items
        ],
        total=page.total,
    )


async def _change_status(
    appointment_id: int,
    principal: Principal,
    change_status: ChangeAppointmentStatus,
    events: EventPublisher,
    labels: AppointmentLabelDirectory,
    target: AppointmentStatus,
    reason: str = "",
) -> AppointmentResponse:
    try:
        appointment = await change_status(
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
    except (IllegalStatusChange, StatusChangeTooEarly) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except InvalidAppointment as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return await _notify_change(events, appointment, labels)


@router.post(
    "/{appointment_id}/confirm",
    response_model=AppointmentResponse,
    summary="Confirmar una cita",
)
async def confirm_appointment(
    appointment_id: int,
    veterinarian: AttendantDep,
    change_status: ChangeStatusDep,
    events: EventPublisherDep,
    labels: AppointmentLabelsDep,
) -> AppointmentResponse:
    return await _change_status(
        appointment_id, veterinarian, change_status, events, labels, AppointmentStatus.CONFIRMED
    )


@router.post(
    "/{appointment_id}/complete",
    response_model=AppointmentResponse,
    summary="Dar por completada una cita",
)
async def complete_appointment(
    appointment_id: int,
    veterinarian: AttendantDep,
    change_status: ChangeStatusDep,
    events: EventPublisherDep,
    labels: AppointmentLabelsDep,
) -> AppointmentResponse:
    return await _change_status(
        appointment_id, veterinarian, change_status, events, labels, AppointmentStatus.COMPLETED
    )


@router.post(
    "/{appointment_id}/no-show",
    response_model=AppointmentResponse,
    summary="Marcar que el cliente no asistió",
)
async def mark_appointment_no_show(
    appointment_id: int,
    veterinarian: AttendantDep,
    change_status: ChangeStatusDep,
    events: EventPublisherDep,
    labels: AppointmentLabelsDep,
) -> AppointmentResponse:
    return await _change_status(
        appointment_id, veterinarian, change_status, events, labels, AppointmentStatus.NO_SHOW
    )


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    summary="Cancelar una cita",
)
async def cancel_appointment(
    appointment_id: int,
    payload: CancelAppointmentRequest,
    principal: CancelerDep,
    change_status: ChangeStatusDep,
    events: EventPublisherDep,
    labels: AppointmentLabelsDep,
) -> AppointmentResponse:
    # Cancelar lo pueden hacer las dos partes: el caso de uso comprueba que
    # quien cancela participe en esa cita.
    return await _change_status(
        appointment_id,
        principal,
        change_status,
        events,
        labels,
        AppointmentStatus.CANCELLED,
        reason=payload.reason,
    )

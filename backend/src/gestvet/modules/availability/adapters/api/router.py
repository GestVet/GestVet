"""Adaptador de entrada HTTP de la agenda.

La administración asigna los turnos y las guardias, de a uno o con un horario
semanal. El veterinario ve los suyos y pide cambios. Quien tenga permiso ve la
agenda de un veterinario. Cada cambio avisa en tiempo real al veterinario
afectado y a la administración.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal, Role
from gestvet.core.permissions import Permission
from gestvet.core.realtime import SCHEDULE_TOPIC, EventPublisher, RealtimeEvent
from gestvet.core.realtime_broker import EventPublisherDep
from gestvet.modules.availability.adapters.api.dependencies import (
    AppointmentDirectoryDep,
    AvailabilityRepositoryDep,
    ChangeRequestRepositoryDep,
    VeterinarianDirectoryDep,
)
from gestvet.modules.availability.adapters.api.schemas import (
    AssignShiftRequest,
    ChangeRequestListResponse,
    ChangeRequestResponse,
    CreateChangeRequest,
    ResolveChangeRequest,
    SlotListResponse,
    SlotResponse,
    WeeklyPlanRequest,
)
from gestvet.modules.availability.domain.entities import (
    AvailabilitySlot,
    ChangeRequestStatus,
    ShiftChangeRequest,
)
from gestvet.modules.availability.domain.exceptions import (
    AvailabilityError,
    ChangeRequestAlreadyResolved,
    ChangeRequestNotFound,
    InvalidChangeRequest,
    InvalidSlot,
    OverlappingSlot,
    ShiftHasAppointments,
    SlotNotFound,
    VeterinarianNotFound,
)
from gestvet.modules.availability.ports.availability_repository import (
    ChangeRequestQuery,
    SlotQuery,
)
from gestvet.modules.availability.use_cases.apply_weekly_plan import (
    ApplyWeeklyPlan,
    ApplyWeeklyPlanCommand,
)
from gestvet.modules.availability.use_cases.assign_shift import AssignShift, AssignShiftCommand
from gestvet.modules.availability.use_cases.change_requests import (
    ListChangeRequests,
    RequestShiftChange,
    RequestShiftChangeCommand,
    ResolveShiftChange,
    ResolveShiftChangeCommand,
)
from gestvet.modules.availability.use_cases.list_slots import ListSlots
from gestvet.modules.availability.use_cases.remove_shift import RemoveShift, RemoveShiftCommand

router = APIRouter()

OwnScheduleDep = Annotated[Principal, Depends(require_permission(Permission.SCHEDULE_READ_OWN))]
SchedulerDep = Annotated[Principal, Depends(require_permission(Permission.SCHEDULE_MANAGE))]
ChangeRequesterDep = Annotated[
    Principal, Depends(require_permission(Permission.SCHEDULE_REQUEST_CHANGE))
]

# Seis semanas: alcanza para ver un mes entero empezando en cualquier día.
MAX_ROSTER_WINDOW = timedelta(days=42)

_STATUS_BY_ERROR: tuple[tuple[type[AvailabilityError], int], ...] = (
    (SlotNotFound, status.HTTP_404_NOT_FOUND),
    (VeterinarianNotFound, status.HTTP_404_NOT_FOUND),
    (ChangeRequestNotFound, status.HTTP_404_NOT_FOUND),
    (OverlappingSlot, status.HTTP_409_CONFLICT),
    (ShiftHasAppointments, status.HTTP_409_CONFLICT),
    (ChangeRequestAlreadyResolved, status.HTTP_409_CONFLICT),
    (InvalidSlot, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidChangeRequest, status.HTTP_422_UNPROCESSABLE_CONTENT),
)

StartsAfter = Annotated[datetime | None, Query(description="Desde")]
EndsBefore = Annotated[datetime | None, Query(description="Hasta")]


def _to_http(error: AvailabilityError) -> HTTPException:
    for error_type, code in _STATUS_BY_ERROR:
        if isinstance(error, error_type):
            return HTTPException(code, str(error))
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(error))


def _notify(events: EventPublisher, veterinarian_id: int) -> None:
    events.publish(
        RealtimeEvent(
            topic=SCHEDULE_TOPIC,
            user_ids=frozenset({veterinarian_id}),
            roles=frozenset({Role.ADMIN}),
        )
    )


def _to_list(slots: list[AvailabilitySlot]) -> SlotListResponse:
    items = [SlotResponse.from_entity(slot) for slot in slots]
    return SlotListResponse(items=items, total=len(items))


def _to_request_list(requests: list[ShiftChangeRequest]) -> ChangeRequestListResponse:
    return ChangeRequestListResponse(
        items=[ChangeRequestResponse.from_entity(request) for request in requests]
    )


@router.get("/mine", response_model=SlotListResponse, summary="Mis turnos y guardias")
async def list_my_slots(
    veterinarian: OwnScheduleDep,
    slots: AvailabilityRepositoryDep,
    starts_after: StartsAfter = None,
    ends_before: EndsBefore = None,
) -> SlotListResponse:
    query = SlotQuery(
        veterinarian_id=veterinarian.user_id, starts_after=starts_after, ends_before=ends_before
    )
    return _to_list(await ListSlots(slots)(query))


@router.get(
    "/roster",
    response_model=SlotListResponse,
    dependencies=[Depends(require_permission(Permission.SCHEDULE_MANAGE))],
    summary="Turnos de todo el equipo",
)
async def list_roster(
    slots: AvailabilityRepositoryDep,
    starts_after: Annotated[datetime, Query(description="Desde")],
    ends_before: Annotated[datetime, Query(description="Hasta")],
) -> SlotListResponse:
    if ends_before <= starts_after or ends_before - starts_after > MAX_ROSTER_WINDOW:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Consulta un rango de hasta {MAX_ROSTER_WINDOW.days} días.",
        )
    query = SlotQuery(starts_after=starts_after, ends_before=ends_before)
    return _to_list(await ListSlots(slots)(query))


@router.get(
    "",
    response_model=SlotListResponse,
    dependencies=[Depends(require_permission(Permission.SCHEDULE_READ))],
    summary="Turnos de un veterinario",
)
async def list_slots_of_veterinarian(
    slots: AvailabilityRepositoryDep,
    veterinarian_id: Annotated[int, Query(ge=1, description="Veterinario consultado")],
    starts_after: StartsAfter = None,
    ends_before: EndsBefore = None,
) -> SlotListResponse:
    query = SlotQuery(
        veterinarian_id=veterinarian_id, starts_after=starts_after, ends_before=ends_before
    )
    return _to_list(await ListSlots(slots)(query))


@router.post(
    "/shifts",
    response_model=SlotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar un turno o una guardia",
)
async def assign_shift(
    payload: AssignShiftRequest,
    scheduler: SchedulerDep,
    slots: AvailabilityRepositoryDep,
    veterinarians: VeterinarianDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> SlotResponse:
    try:
        slot = await AssignShift(slots, veterinarians, activity)(
            AssignShiftCommand(
                actor_id=scheduler.user_id,
                veterinarian_id=payload.veterinarian_id,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                kind=payload.kind,
                now=datetime.now(UTC),
            )
        )
    except AvailabilityError as error:
        raise _to_http(error) from error
    _notify(events, slot.veterinarian_id)
    return SlotResponse.from_entity(slot)


@router.post(
    "/weekly-plan",
    response_model=SlotListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aplicar un horario semanal",
)
async def apply_weekly_plan(
    payload: WeeklyPlanRequest,
    scheduler: SchedulerDep,
    slots: AvailabilityRepositoryDep,
    veterinarians: VeterinarianDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> SlotListResponse:
    try:
        creados = await ApplyWeeklyPlan(slots, veterinarians, activity)(
            ApplyWeeklyPlanCommand(
                actor_id=scheduler.user_id,
                veterinarian_id=payload.veterinarian_id,
                first_day=payload.first_day,
                weeks=payload.weeks,
                shifts=tuple(item.to_domain() for item in payload.shifts),
                now=datetime.now(UTC),
            )
        )
    except AvailabilityError as error:
        raise _to_http(error) from error
    _notify(events, payload.veterinarian_id)
    return _to_list(creados)


@router.delete(
    "/shifts/{slot_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Quitar un turno"
)
async def remove_shift(
    slot_id: int,
    scheduler: SchedulerDep,
    slots: AvailabilityRepositoryDep,
    appointments: AppointmentDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> None:
    try:
        quitado = await RemoveShift(slots, appointments, activity)(
            RemoveShiftCommand(actor_id=scheduler.user_id, slot_id=slot_id)
        )
    except AvailabilityError as error:
        raise _to_http(error) from error
    _notify(events, quitado.veterinarian_id)


@router.post(
    "/change-requests",
    response_model=ChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pedir un cambio de turno",
)
async def request_change(
    payload: CreateChangeRequest,
    veterinarian: ChangeRequesterDep,
    requests: ChangeRequestRepositoryDep,
    slots: AvailabilityRepositoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> ChangeRequestResponse:
    try:
        pedido = await RequestShiftChange(requests, slots, activity)(
            RequestShiftChangeCommand(
                veterinarian_id=veterinarian.user_id,
                message=payload.message,
                slot_id=payload.slot_id,
            )
        )
    except AvailabilityError as error:
        raise _to_http(error) from error
    _notify(events, pedido.veterinarian_id)
    return ChangeRequestResponse.from_entity(pedido)


@router.get(
    "/change-requests/mine",
    response_model=ChangeRequestListResponse,
    summary="Mis pedidos de cambio",
)
async def list_my_change_requests(
    veterinarian: ChangeRequesterDep, requests: ChangeRequestRepositoryDep
) -> ChangeRequestListResponse:
    query = ChangeRequestQuery(veterinarian_id=veterinarian.user_id)
    return _to_request_list(await ListChangeRequests(requests)(query))


@router.get(
    "/change-requests",
    response_model=ChangeRequestListResponse,
    dependencies=[Depends(require_permission(Permission.SCHEDULE_MANAGE))],
    summary="Pedidos de cambio del equipo",
)
async def list_change_requests(
    requests: ChangeRequestRepositoryDep,
    status_filter: Annotated[
        ChangeRequestStatus | None, Query(alias="status", description="Estado")
    ] = None,
) -> ChangeRequestListResponse:
    query = ChangeRequestQuery(status=status_filter)
    return _to_request_list(await ListChangeRequests(requests)(query))


@router.post(
    "/change-requests/{request_id}/resolve",
    response_model=ChangeRequestResponse,
    summary="Responder un pedido de cambio",
)
async def resolve_change_request(
    request_id: int,
    payload: ResolveChangeRequest,
    scheduler: SchedulerDep,
    requests: ChangeRequestRepositoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> ChangeRequestResponse:
    try:
        pedido = await ResolveShiftChange(requests, activity)(
            ResolveShiftChangeCommand(
                actor_id=scheduler.user_id,
                request_id=request_id,
                accepted=payload.accepted,
                response=payload.response,
                now=datetime.now(UTC),
            )
        )
    except AvailabilityError as error:
        raise _to_http(error) from error
    _notify(events, pedido.veterinarian_id)
    return ChangeRequestResponse.from_entity(pedido)

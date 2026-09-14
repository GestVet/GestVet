"""Casos de uso de los pedidos de cambio de turno."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.availability.domain.entities import ShiftChangeRequest
from gestvet.modules.availability.domain.exceptions import ChangeRequestNotFound, SlotNotFound
from gestvet.modules.availability.ports.availability_repository import (
    AvailabilityRepository,
    ChangeRequestQuery,
    ShiftChangeRequestRepository,
)

# Lo que entra del mensaje en la bitácora: alcanza para reconocer el pedido.
_DETAIL_LENGTH = 80


@dataclass(frozen=True, slots=True)
class RequestShiftChangeCommand:
    veterinarian_id: int
    message: str
    slot_id: int | None = None


class RequestShiftChange:
    def __init__(
        self,
        requests: ShiftChangeRequestRepository,
        slots: AvailabilityRepository,
        activity: ActivityRecorder,
    ) -> None:
        self._requests = requests
        self._slots = slots
        self._activity = activity

    async def __call__(self, command: RequestShiftChangeCommand) -> ShiftChangeRequest:
        # Se pide sobre un turno propio. El de otro veterinario responde que no
        # existe, igual que cualquier recurso ajeno.
        if (
            command.slot_id is not None
            and await self._slots.get(command.slot_id, command.veterinarian_id) is None
        ):
            raise SlotNotFound(command.slot_id)

        pedido = await self._requests.add(
            ShiftChangeRequest(
                veterinarian_id=command.veterinarian_id,
                message=command.message,
                slot_id=command.slot_id,
            )
        )
        await self._activity.record(
            command.veterinarian_id,
            ActivityKind.SHIFT_CHANGE_REQUESTED,
            pedido.message[:_DETAIL_LENGTH],
        )
        return pedido


@dataclass(frozen=True, slots=True)
class ResolveShiftChangeCommand:
    actor_id: int
    request_id: int
    accepted: bool
    response: str
    now: datetime


class ResolveShiftChange:
    def __init__(self, requests: ShiftChangeRequestRepository, activity: ActivityRecorder) -> None:
        self._requests = requests
        self._activity = activity

    async def __call__(self, command: ResolveShiftChangeCommand) -> ShiftChangeRequest:
        pedido = await self._requests.get(command.request_id)
        if pedido is None:
            raise ChangeRequestNotFound(command.request_id)

        pedido.resolve(command.actor_id, command.accepted, command.response, command.now)
        guardado = await self._requests.save(pedido)
        veredicto = "Aceptó" if command.accepted else "Rechazó"
        await self._activity.record(
            command.actor_id,
            ActivityKind.SHIFT_CHANGE_RESOLVED,
            f"{veredicto} el pedido #{guardado.id} del veterinario #{guardado.veterinarian_id}",
        )
        return guardado


class ListChangeRequests:
    def __init__(self, requests: ShiftChangeRequestRepository) -> None:
        self._requests = requests

    async def __call__(self, query: ChangeRequestQuery) -> list[ShiftChangeRequest]:
        return await self._requests.list(query)

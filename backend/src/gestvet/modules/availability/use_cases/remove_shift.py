"""Caso de uso: quitar un turno."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.availability.domain.entities import AvailabilitySlot
from gestvet.modules.availability.domain.exceptions import ShiftHasAppointments, SlotNotFound
from gestvet.modules.availability.ports.availability_repository import (
    AppointmentDirectory,
    AvailabilityRepository,
)
from gestvet.modules.availability.use_cases.assign_shift import describe_shift


@dataclass(frozen=True, slots=True)
class RemoveShiftCommand:
    actor_id: int
    slot_id: int


class RemoveShift:
    def __init__(
        self,
        slots: AvailabilityRepository,
        appointments: AppointmentDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._slots = slots
        self._appointments = appointments
        self._activity = activity

    async def __call__(self, command: RemoveShiftCommand) -> AvailabilitySlot:
        turno = await self._slots.get(command.slot_id)
        if turno is None:
            raise SlotNotFound(command.slot_id)

        # Quitar el turno dejaría esas citas fuera de horario y sin nadie que
        # avise al cliente.
        if await self._appointments.has_active_appointments(
            turno.veterinarian_id, turno.starts_at, turno.ends_at
        ):
            raise ShiftHasAppointments(command.slot_id)

        if not await self._slots.delete(command.slot_id):
            raise SlotNotFound(command.slot_id)
        await self._activity.record(
            command.actor_id, ActivityKind.SHIFT_REMOVED, describe_shift(turno)
        )
        return turno

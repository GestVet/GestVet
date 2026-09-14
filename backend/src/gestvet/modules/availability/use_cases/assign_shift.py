"""Caso de uso: asignar un turno o una guardia a un veterinario."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.clinic_time import CLINIC_UTC_OFFSET
from gestvet.modules.availability.domain.entities import (
    AvailabilitySlot,
    ShiftKind,
    ensure_schedulable,
)
from gestvet.modules.availability.domain.exceptions import OverlappingSlot, VeterinarianNotFound
from gestvet.modules.availability.ports.availability_repository import (
    AvailabilityRepository,
    VeterinarianDirectory,
)


@dataclass(frozen=True, slots=True)
class AssignShiftCommand:
    actor_id: int
    veterinarian_id: int
    starts_at: datetime
    ends_at: datetime
    kind: ShiftKind
    now: datetime


async def require_veterinarian(veterinarians: VeterinarianDirectory, veterinarian_id: int) -> None:
    if not await veterinarians.is_active_veterinarian(veterinarian_id):
        raise VeterinarianNotFound(veterinarian_id)


def describe_shift(slot: AvailabilitySlot) -> str:
    """Turno legible para la bitácora, en la hora de la clínica."""
    inicio = slot.starts_at + CLINIC_UTC_OFFSET
    fin = slot.ends_at + CLINIC_UTC_OFFSET
    return (
        f"{slot.kind.label} del veterinario #{slot.veterinarian_id}: "
        f"{inicio:%d/%m/%Y %H:%M} a {fin:%d/%m/%Y %H:%M}"
    )


class AssignShift:
    def __init__(
        self,
        slots: AvailabilityRepository,
        veterinarians: VeterinarianDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._slots = slots
        self._veterinarians = veterinarians
        self._activity = activity

    async def __call__(self, command: AssignShiftCommand) -> AvailabilitySlot:
        await require_veterinarian(self._veterinarians, command.veterinarian_id)
        slot = AvailabilitySlot(
            veterinarian_id=command.veterinarian_id,
            starts_at=command.starts_at,
            ends_at=command.ends_at,
            kind=command.kind,
            assigned_by=command.actor_id,
        )
        ensure_schedulable(slot, command.now)

        # Dos turnos superpuestos harían que la agenda ofrezca dos veces la misma
        # hora, o que nadie sepa si esa noche atiende o está de guardia.
        if await self._slots.find_overlapping(slot.veterinarian_id, slot.starts_at, slot.ends_at):
            raise OverlappingSlot()

        asignado = await self._slots.add(slot)
        await self._activity.record(
            command.actor_id, ActivityKind.SHIFT_ASSIGNED, describe_shift(asignado)
        )
        return asignado

"""Caso de uso: publicar un tramo de disponibilidad."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gestvet.modules.availability.domain.entities import AvailabilitySlot
from gestvet.modules.availability.domain.exceptions import OverlappingSlot
from gestvet.modules.availability.ports.availability_repository import AvailabilityRepository


@dataclass(frozen=True, slots=True)
class PublishSlotCommand:
    veterinarian_id: int
    starts_at: datetime
    ends_at: datetime


class PublishSlot:
    def __init__(self, slots: AvailabilityRepository) -> None:
        self._slots = slots

    async def __call__(self, command: PublishSlotCommand) -> AvailabilitySlot:
        slot = AvailabilitySlot(
            veterinarian_id=command.veterinarian_id,
            starts_at=command.starts_at,
            ends_at=command.ends_at,
        )

        # El original dejaba publicar tramos superpuestos, y después la agenda
        # ofrecía dos veces la misma hora.
        if await self._slots.find_overlapping(slot.veterinarian_id, slot.starts_at, slot.ends_at):
            raise OverlappingSlot()

        return await self._slots.add(slot)

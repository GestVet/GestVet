from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.availability.domain.entities import AvailabilitySlot
from gestvet.modules.availability.domain.exceptions import OverlappingSlot
from gestvet.modules.availability.ports.availability_repository import AvailabilityRepository


@dataclass(frozen=True, slots=True)
class PublishSlotCommand:
    veterinarian_id: int
    starts_at: datetime
    ends_at: datetime


class PublishSlot:
    def __init__(self, slots: AvailabilityRepository, activity: ActivityRecorder) -> None:
        self._slots = slots
        self._activity = activity

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

        publicado = await self._slots.add(slot)
        await self._activity.record(
            publicado.veterinarian_id,
            ActivityKind.SLOT_PUBLISHED,
            _rango(publicado.starts_at, publicado.ends_at),
        )
        return publicado


def _rango(inicio: datetime, fin: datetime) -> str:
    """Rango legible para la bitácora, en UTC y sin segundos."""
    return f"{inicio:%d/%m/%Y %H:%M} a {fin:%d/%m/%Y %H:%M} UTC"

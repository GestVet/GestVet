from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.availability.domain.exceptions import SlotNotFound
from gestvet.modules.availability.ports.availability_repository import AvailabilityRepository


@dataclass(frozen=True, slots=True)
class WithdrawSlotCommand:
    slot_id: int
    veterinarian_id: int


class WithdrawSlot:
    def __init__(self, slots: AvailabilityRepository, activity: ActivityRecorder) -> None:
        self._slots = slots
        self._activity = activity

    async def __call__(self, command: WithdrawSlotCommand) -> None:
        # La propiedad se aplica en la consulta: retirar el tramo de otro
        # veterinario responde que no existe. Se lee antes de borrar para poder
        # dejar en la bitacora que tramo era.
        tramo = await self._slots.get(command.slot_id, command.veterinarian_id)
        if tramo is None or not await self._slots.delete(command.slot_id, command.veterinarian_id):
            raise SlotNotFound(command.slot_id)

        await self._activity.record(
            command.veterinarian_id,
            ActivityKind.SLOT_WITHDRAWN,
            f"{tramo.starts_at:%d/%m/%Y %H:%M} a {tramo.ends_at:%d/%m/%Y %H:%M} UTC",
        )

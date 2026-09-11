"""Caso de uso: retirar un tramo de disponibilidad propio."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.modules.availability.domain.exceptions import SlotNotFound
from gestvet.modules.availability.ports.availability_repository import AvailabilityRepository


@dataclass(frozen=True, slots=True)
class WithdrawSlotCommand:
    slot_id: int
    veterinarian_id: int


class WithdrawSlot:
    def __init__(self, slots: AvailabilityRepository) -> None:
        self._slots = slots

    async def __call__(self, command: WithdrawSlotCommand) -> None:
        # La propiedad se aplica en la consulta: retirar el tramo de otro
        # veterinario responde que no existe.
        if not await self._slots.delete(command.slot_id, command.veterinarian_id):
            raise SlotNotFound(command.slot_id)

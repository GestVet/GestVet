"""Caso de uso: consultar la agenda publicada de un veterinario."""

from __future__ import annotations

from gestvet.availability.domain.entities import AvailabilitySlot
from gestvet.availability.ports.availability_repository import (
    AvailabilityRepository,
    SlotQuery,
)


class ListSlots:
    def __init__(self, slots: AvailabilityRepository) -> None:
        self._slots = slots

    async def __call__(self, query: SlotQuery) -> list[AvailabilitySlot]:
        return await self._slots.list(query)

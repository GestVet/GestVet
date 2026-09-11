from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from gestvet.modules.availability.domain.entities import AvailabilitySlot


@dataclass(frozen=True, slots=True)
class SlotQuery:
    veterinarian_id: int | None = None
    starts_after: datetime | None = None
    ends_before: datetime | None = None


class AvailabilityRepository(Protocol):
    async def add(self, slot: AvailabilitySlot) -> AvailabilitySlot: ...

    async def get(
        self, slot_id: int, veterinarian_id: int | None = None
    ) -> AvailabilitySlot | None: ...

    async def list(self, query: SlotQuery) -> list[AvailabilitySlot]: ...

    async def find_overlapping(
        self, veterinarian_id: int, starts_at: datetime, ends_at: datetime
    ) -> list[AvailabilitySlot]: ...

    async def delete(self, slot_id: int, veterinarian_id: int) -> bool: ...

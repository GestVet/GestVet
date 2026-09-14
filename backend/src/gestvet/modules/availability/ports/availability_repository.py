"""Puertos del módulo de agenda.

Los dos repositorios son de persistencia propia. Los dos lectores son preguntas
a datos de otros módulos: si una cuenta es un veterinario activo, y si un turno
tiene citas reservadas. Se leen, nunca se escriben.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from gestvet.modules.availability.domain.entities import (
    AvailabilitySlot,
    ChangeRequestStatus,
    ShiftChangeRequest,
)


@dataclass(frozen=True, slots=True)
class SlotQuery:
    veterinarian_id: int | None = None
    starts_after: datetime | None = None
    ends_before: datetime | None = None


class AvailabilityRepository(Protocol):
    async def add(self, slot: AvailabilitySlot) -> AvailabilitySlot: ...

    async def add_many(self, slots: list[AvailabilitySlot]) -> list[AvailabilitySlot]: ...

    async def get(
        self, slot_id: int, veterinarian_id: int | None = None
    ) -> AvailabilitySlot | None: ...

    async def list(self, query: SlotQuery) -> list[AvailabilitySlot]: ...

    async def find_overlapping(
        self, veterinarian_id: int, starts_at: datetime, ends_at: datetime
    ) -> list[AvailabilitySlot]: ...

    async def delete(self, slot_id: int) -> bool: ...


@dataclass(frozen=True, slots=True)
class ChangeRequestQuery:
    veterinarian_id: int | None = None
    status: ChangeRequestStatus | None = None


class ShiftChangeRequestRepository(Protocol):
    async def add(self, request: ShiftChangeRequest) -> ShiftChangeRequest: ...

    async def get(self, request_id: int) -> ShiftChangeRequest | None: ...

    async def save(self, request: ShiftChangeRequest) -> ShiftChangeRequest: ...

    async def list(self, query: ChangeRequestQuery) -> list[ShiftChangeRequest]: ...


class VeterinarianDirectory(Protocol):
    """Lo que la agenda necesita saber de una cuenta: si es un veterinario activo."""

    async def is_active_veterinarian(self, user_id: int) -> bool: ...


class AppointmentDirectory(Protocol):
    """Lo que la agenda necesita saber de las citas: si un turno ya tiene alguna."""

    async def has_active_appointments(
        self, veterinarian_id: int, starts_at: datetime, ends_at: datetime
    ) -> bool: ...

"""Puertos del módulo de citas.

Los tres primeros son de persistencia propia. Los dos últimos son *lectores*:
preguntas que el negocio le hace a datos que posee otro módulo.

Un lector existe porque los módulos de dominio no se importan entre sí. La cita
necesita saber si la mascota es del cliente y si el veterinario tiene turno a
esa hora, pero no puede llamar a `pets` ni a `availability`. Declara la pregunta
acá y un adaptador la responde leyendo la tabla del otro módulo, igual que hace
`gestvet.core.auth` con la de usuarios. Es una lectura, nunca una escritura.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page
from gestvet.modules.appointments.domain.entities import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
)


@dataclass(frozen=True, slots=True)
class AppointmentQuery:
    client_id: int | None = None
    veterinarian_id: int | None = None
    pet_id: int | None = None
    statuses: frozenset[AppointmentStatus] | None = None
    is_emergency: bool | None = None
    starts_after: datetime | None = None
    ends_before: datetime | None = None
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


class AppointmentRepository(Protocol):
    async def add(self, appointment: Appointment) -> Appointment: ...

    async def get(self, appointment_id: int) -> Appointment | None: ...

    async def save(self, appointment: Appointment) -> Appointment: ...

    async def search(self, query: AppointmentQuery) -> Page[Appointment]: ...

    async def find_conflicting(
        self, veterinarian_id: int, starts_at: datetime, ends_at: datetime
    ) -> list[Appointment]: ...

    async def find_due_for_reminder(
        self, window_start: datetime, window_end: datetime
    ) -> list[Appointment]: ...

    async def count_active_for(self, veterinarian_id: int) -> int: ...


class AppointmentTypeRepository(Protocol):
    async def get(self, type_id: int) -> AppointmentType | None: ...

    async def list_active(self, include_emergency: bool = False) -> list[AppointmentType]: ...

    async def get_emergency(self) -> AppointmentType | None: ...


class PetDirectory(Protocol):
    """Lo que las citas necesitan saber de una mascota: de quién es y su nombre."""

    async def is_owned_by(self, pet_id: int, owner_id: int) -> bool: ...

    async def find_name(self, pet_id: int) -> str | None: ...


@dataclass(frozen=True, slots=True)
class ScheduleSlot:
    """Un tramo publicado, visto desde las citas: de quién es y cuándo."""

    veterinarian_id: int
    starts_at: datetime
    ends_at: datetime


class ScheduleDirectory(Protocol):
    """Lo que las citas necesitan saber de la agenda y de a quién atiende."""

    async def bookable_slots_between(
        self, starts_at: datetime, ends_at: datetime
    ) -> list[ScheduleSlot]: ...

    async def covers(
        self, veterinarian_id: int, starts_at: datetime, ends_at: datetime
    ) -> bool: ...

    async def veterinarians_on_duty(self, moment: datetime) -> list[int]: ...

    async def is_bookable_for_normal_appointments(self, veterinarian_id: int) -> bool: ...

    async def veterinarians_working(self, moment: datetime) -> list[int]: ...

"""Caso de uso: horas libres para reservar.

La persona elige primero el día y después una hora de un veterinario, en vez de
escribir una fecha y esperar a que el servidor la rechace. Para eso hace falta
calcular qué horas caben, y el cálculo aplica las mismas reglas que la reserva:

- la cita entera cabe en un tramo publicado;
- no pisa otra cita activa del veterinario, con el margen entre citas;
- el veterinario no está cubriendo una emergencia ese día;
- la hora todavía no pasó.

Lo calcula el servidor porque un cliente no puede ver las citas de otros, que
son justamente las que ocupan las horas.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from gestvet.core.clinic_time import clinic_date, clinic_midnight
from gestvet.core.pagination import MAX_PAGE_SIZE
from gestvet.modules.appointments.domain.entities import (
    ACTIVE_STATUSES,
    Appointment,
)
from gestvet.modules.appointments.domain.exceptions import InvalidAppointment
from gestvet.modules.appointments.ports.repositories import (
    AppointmentQuery,
    AppointmentRepository,
    AppointmentTypeRepository,
    ScheduleDirectory,
    ScheduleSlot,
)
from gestvet.modules.appointments.use_cases.book_appointment import require_bookable_type

# Las horas se ofrecen cada cuarto de hora: da opciones de sobra sin volver la
# lista interminable.
SLOT_STEP = timedelta(minutes=15)
MAX_DAYS = 31
_STEP_EPOCH = datetime(2000, 1, 1, tzinfo=UTC)


def _ceil_to_step(moment: datetime) -> datetime:
    remainder = (moment - _STEP_EPOCH) % SLOT_STEP
    return moment if not remainder else moment + (SLOT_STEP - remainder)


@dataclass(frozen=True, slots=True)
class OpenTimesQuery:
    appointment_type_id: int
    first_day: date
    days: int
    now: datetime


@dataclass(frozen=True, slots=True)
class VeterinarianOpenTimes:
    veterinarian_id: int
    times: tuple[datetime, ...]


@dataclass(frozen=True, slots=True)
class DayOpenTimes:
    day: date
    veterinarians: tuple[VeterinarianOpenTimes, ...]


class ListOpenTimes:
    def __init__(
        self,
        appointments: AppointmentRepository,
        types: AppointmentTypeRepository,
        schedule: ScheduleDirectory,
    ) -> None:
        self._appointments = appointments
        self._types = types
        self._schedule = schedule

    async def __call__(self, query: OpenTimesQuery) -> list[DayOpenTimes]:
        if not 1 <= query.days <= MAX_DAYS:
            raise InvalidAppointment(f"Se pueden consultar entre 1 y {MAX_DAYS} días.")
        appointment_type = await require_bookable_type(self._types, query.appointment_type_id)

        window_start = clinic_midnight(query.first_day)
        window_end = window_start + timedelta(days=query.days)
        slots = await self._schedule.bookable_slots_between(window_start, window_end)
        busy = await self._busy_by_veterinarian(slots, window_start, window_end)
        covering = await self._days_covering_emergencies(window_start, window_end)

        found: defaultdict[date, defaultdict[int, set[datetime]]] = defaultdict(
            lambda: defaultdict(set)
        )
        earliest = max(query.now, window_start)
        for slot in slots:
            starts = _fitting_starts(slot, appointment_type.duration, earliest, window_end)
            for start in starts:
                day = clinic_date(start)
                if (slot.veterinarian_id, day) in covering:
                    continue
                ends = start + appointment_type.duration
                if any(cita.overlaps(start, ends) for cita in busy[slot.veterinarian_id]):
                    continue
                found[day][slot.veterinarian_id].add(start)

        return [
            DayOpenTimes(
                day=day,
                veterinarians=tuple(
                    VeterinarianOpenTimes(veterinarian_id=vet, times=tuple(sorted(times)))
                    for vet, times in sorted(found[day].items())
                ),
            )
            for day in sorted(found)
        ]

    async def _busy_by_veterinarian(
        self, slots: list[ScheduleSlot], starts_at: datetime, ends_at: datetime
    ) -> dict[int, list[Appointment]]:
        veterinarians = {slot.veterinarian_id for slot in slots}
        return {
            vet: await self._appointments.find_conflicting(vet, starts_at, ends_at)
            for vet in veterinarians
        }

    async def _days_covering_emergencies(
        self, starts_at: datetime, ends_at: datetime
    ) -> set[tuple[int, date]]:
        """Un veterinario con una emergencia activa no recibe citas normales ese día."""
        emergencias = await self._appointments.search(
            AppointmentQuery(
                is_emergency=True,
                statuses=ACTIVE_STATUSES,
                starts_after=starts_at,
                ends_before=ends_at,
                limit=MAX_PAGE_SIZE,
            )
        )
        return {
            (cita.veterinarian_id, clinic_date(cita.scheduled_at)) for cita in emergencias.items
        }


def _fitting_starts(
    slot: ScheduleSlot, duration: timedelta, earliest: datetime, window_end: datetime
) -> Iterator[datetime]:
    """Cada cuarto de hora del tramo en el que la cita entera todavía cabe."""
    start = _ceil_to_step(max(slot.starts_at, earliest))
    while start + duration <= slot.ends_at and start < window_end:
        yield start
        start += SLOT_STEP

"""Caso de uso: la grilla de horas de cada turno, con lo que se puede reservar.

La persona elige primero el día y después una hora de un veterinario, en vez de
escribir una fecha y esperar a que el servidor la rechace. Cada cuarto de hora
del turno sale con su estado, y solo queda libre si cumple las mismas reglas
que la reserva:

- la hora todavía no pasó;
- el veterinario no está cubriendo una emergencia ese día;
- la cita entera cabe antes de que termine el tramo publicado;
- no pisa otra cita activa del veterinario, con el margen entre citas.

Las horas que no cumplen se devuelven igual, con el motivo: una hora que
desaparece no le explica a nadie por qué no la puede tomar.

Lo calcula el servidor porque un cliente no puede ver las citas de otros, que
son justamente las que ocupan las horas.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum

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


class SlotStatus(StrEnum):
    AVAILABLE = "available"
    TAKEN = "taken"
    TOO_SHORT = "too_short"
    PAST = "past"
    EMERGENCY = "emergency"


@dataclass(frozen=True, slots=True)
class ScheduleWindow:
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True, slots=True)
class GridSlot:
    time: datetime
    status: SlotStatus


@dataclass(frozen=True, slots=True)
class VeterinarianOpenTimes:
    veterinarian_id: int
    windows: tuple[ScheduleWindow, ...]
    slots: tuple[GridSlot, ...]


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

        grid: defaultdict[date, defaultdict[int, dict[datetime, SlotStatus]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        windows: defaultdict[date, defaultdict[int, list[ScheduleWindow]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for slot in slots:
            vet = slot.veterinarian_id
            days_of_slot: set[date] = set()
            for start in _grid_starts(slot, window_start, window_end):
                day = clinic_date(start)
                days_of_slot.add(day)
                status = _classify(
                    start,
                    slot,
                    appointment_type.duration,
                    now=query.now,
                    covering=(vet, day) in covering,
                    busy=busy[vet],
                )
                grid[day][vet][start] = status
            for day in days_of_slot:
                windows[day][vet].append(ScheduleWindow(slot.starts_at, slot.ends_at))

        return [
            DayOpenTimes(
                day=day,
                veterinarians=tuple(
                    VeterinarianOpenTimes(
                        veterinarian_id=vet,
                        windows=tuple(sorted(windows[day][vet], key=lambda w: w.starts_at)),
                        slots=tuple(
                            GridSlot(time=start, status=status)
                            for start, status in sorted(by_time.items())
                        ),
                    )
                    for vet, by_time in sorted(grid[day].items())
                ),
            )
            for day in sorted(grid)
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


def _grid_starts(
    slot: ScheduleSlot, window_start: datetime, window_end: datetime
) -> Iterator[datetime]:
    """Cada cuarto de hora del tramo dentro de la ventana consultada, quepa o no la cita."""
    start = _ceil_to_step(max(slot.starts_at, window_start))
    end = min(slot.ends_at, window_end)
    while start < end:
        yield start
        start += SLOT_STEP


def _classify(
    start: datetime,
    slot: ScheduleSlot,
    duration: timedelta,
    *,
    now: datetime,
    covering: bool,
    busy: list[Appointment],
) -> SlotStatus:
    if start < now:
        return SlotStatus.PAST
    if covering:
        return SlotStatus.EMERGENCY
    ends = start + duration
    if ends > slot.ends_at:
        return SlotStatus.TOO_SHORT
    if any(cita.overlaps(start, ends) for cita in busy):
        return SlotStatus.TAKEN
    return SlotStatus.AVAILABLE

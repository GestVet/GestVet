"""Horario semanal: los mismos turnos repetidos varias semanas.

Así planifica una clínica: "Lucía atiende de lunes a sábado de 9 a 18, Pedro
hace guardia martes y jueves de 20 a 8". Cargar cada día a mano es lento y deja
huecos; el horario se expande en turnos concretos, que después se pueden quitar
o cambiar de a uno.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from itertools import pairwise

from gestvet.core.clinic_time import clinic_midnight
from gestvet.modules.availability.domain.entities import AvailabilitySlot, ShiftKind
from gestvet.modules.availability.domain.exceptions import InvalidSlot, OverlappingSlot

MAX_PLAN_WEEKS = 12
_DAYS_IN_WEEK = 7


@dataclass(frozen=True, slots=True)
class WeeklyShift:
    # 0 es lunes y 6 domingo, igual que `date.weekday()`.
    weekday: int
    starts: time
    ends: time
    kind: ShiftKind = ShiftKind.REGULAR

    def __post_init__(self) -> None:
        if not 0 <= self.weekday < _DAYS_IN_WEEK:
            raise InvalidSlot("El día de la semana va de lunes (0) a domingo (6).")

    def on(self, day: date, veterinarian_id: int, assigned_by: int | None) -> AvailabilitySlot:
        # Un fin igual o anterior al inicio termina al día siguiente: de 20 a 8.
        ends_day = day if self.ends > self.starts else day + timedelta(days=1)
        return AvailabilitySlot(
            veterinarian_id=veterinarian_id,
            starts_at=_at(day, self.starts),
            ends_at=_at(ends_day, self.ends),
            kind=self.kind,
            assigned_by=assigned_by,
        )


def _at(day: date, moment: time) -> datetime:
    return clinic_midnight(day) + timedelta(hours=moment.hour, minutes=moment.minute)


def _days(first_day: date, weeks: int) -> Iterator[date]:
    for offset in range(weeks * _DAYS_IN_WEEK):
        yield first_day + timedelta(days=offset)


def expand_weekly_plan(
    veterinarian_id: int,
    first_day: date,
    weeks: int,
    shifts: Sequence[WeeklyShift],
    assigned_by: int | None = None,
) -> list[AvailabilitySlot]:
    if not 1 <= weeks <= MAX_PLAN_WEEKS:
        raise InvalidSlot(f"Un horario se aplica de 1 a {MAX_PLAN_WEEKS} semanas.")
    if not shifts:
        raise InvalidSlot("Elige al menos un día con su horario.")

    slots = sorted(
        (
            shift.on(day, veterinarian_id, assigned_by)
            for day in _days(first_day, weeks)
            for shift in shifts
            if day.weekday() == shift.weekday
        ),
        key=lambda slot: slot.starts_at,
    )
    # Dos turnos del mismo horario que se pisan son un error de carga: una
    # guardia de 20 a 8 del lunes y un turno de 7 del martes, por ejemplo.
    for previous, current in pairwise(slots):
        if previous.overlaps(current):
            raise OverlappingSlot(current.starts_at)
    return slots

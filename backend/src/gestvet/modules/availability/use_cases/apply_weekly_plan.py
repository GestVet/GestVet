"""Caso de uso: aplicar un horario semanal a un veterinario."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.availability.domain.entities import AvailabilitySlot, ensure_schedulable
from gestvet.modules.availability.domain.exceptions import OverlappingSlot
from gestvet.modules.availability.domain.weekly_plan import WeeklyShift, expand_weekly_plan
from gestvet.modules.availability.ports.availability_repository import (
    AvailabilityRepository,
    VeterinarianDirectory,
)
from gestvet.modules.availability.use_cases.assign_shift import require_veterinarian


@dataclass(frozen=True, slots=True)
class ApplyWeeklyPlanCommand:
    actor_id: int
    veterinarian_id: int
    first_day: date
    weeks: int
    shifts: tuple[WeeklyShift, ...]
    now: datetime


class ApplyWeeklyPlan:
    def __init__(
        self,
        slots: AvailabilityRepository,
        veterinarians: VeterinarianDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._slots = slots
        self._veterinarians = veterinarians
        self._activity = activity

    async def __call__(self, command: ApplyWeeklyPlanCommand) -> list[AvailabilitySlot]:
        await require_veterinarian(self._veterinarians, command.veterinarian_id)
        turnos = expand_weekly_plan(
            command.veterinarian_id,
            command.first_day,
            command.weeks,
            command.shifts,
            assigned_by=command.actor_id,
        )

        # Se aplica entero o no se aplica: un horario a medias es peor que ninguno, porque
        # nadie sabe qué días quedaron sin cubrir.
        for turno in turnos:
            ensure_schedulable(turno, command.now)
            if await self._slots.find_overlapping(
                turno.veterinarian_id, turno.starts_at, turno.ends_at
            ):
                raise OverlappingSlot(turno.starts_at)

        creados = await self._slots.add_many(turnos)
        await self._activity.record(
            command.actor_id,
            ActivityKind.WEEKLY_PLAN_APPLIED,
            f"{len(creados)} turnos del veterinario #{command.veterinarian_id} "
            f"desde el {command.first_day:%d/%m/%Y}",
        )
        return creados

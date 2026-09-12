"""Caso de uso: dar de alta una internación."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.hospitalizations.domain.entities import Hospitalization
from gestvet.modules.hospitalizations.domain.exceptions import HospitalizationNotFound
from gestvet.modules.hospitalizations.ports.hospitalization_repository import (
    HospitalizationRepository,
)


@dataclass(frozen=True, slots=True)
class DischargeHospitalizationCommand:
    hospitalization_id: int
    actor_id: int
    discharge_notes: str


class DischargeHospitalization:
    def __init__(
        self, hospitalizations: HospitalizationRepository, activity: ActivityRecorder
    ) -> None:
        self._hospitalizations = hospitalizations
        self._activity = activity

    async def __call__(self, command: DischargeHospitalizationCommand) -> Hospitalization:
        hospitalization = await self._hospitalizations.get(command.hospitalization_id)
        if hospitalization is None:
            raise HospitalizationNotFound(command.hospitalization_id)

        hospitalization.discharge(command.discharge_notes)
        guardada = await self._hospitalizations.save(hospitalization)
        await self._activity.record(
            command.actor_id, ActivityKind.HOSPITALIZATION_DISCHARGED, guardada.reason
        )
        return guardada

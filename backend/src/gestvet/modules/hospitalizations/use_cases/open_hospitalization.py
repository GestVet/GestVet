"""Caso de uso: abrir una internación a partir de una cita."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.hospitalizations.domain.entities import Hospitalization
from gestvet.modules.hospitalizations.domain.exceptions import AppointmentNotFound
from gestvet.modules.hospitalizations.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.hospitalizations.ports.hospitalization_repository import (
    HospitalizationRepository,
)


@dataclass(frozen=True, slots=True)
class OpenHospitalizationCommand:
    appointment_id: int
    opened_by: int
    reason: str


class OpenHospitalization:
    def __init__(
        self,
        hospitalizations: HospitalizationRepository,
        appointments: AppointmentDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._hospitalizations = hospitalizations
        self._appointments = appointments
        self._activity = activity

    async def __call__(self, command: OpenHospitalizationCommand) -> Hospitalization:
        pet_id = await self._appointments.find_pet_id(command.appointment_id)
        if pet_id is None:
            raise AppointmentNotFound(command.appointment_id)

        hospitalization = Hospitalization(
            appointment_id=command.appointment_id,
            pet_id=pet_id,
            opened_by=command.opened_by,
            reason=command.reason,
        )
        guardada = await self._hospitalizations.add(hospitalization)
        await self._activity.record(
            command.opened_by, ActivityKind.HOSPITALIZATION_OPENED, guardada.reason
        )
        return guardada

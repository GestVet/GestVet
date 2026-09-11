"""Caso de uso: abrir una cita de emergencia.

El cliente no elige veterinario ni hora: la emergencia es ahora y el sistema
asigna al que esté de guardia. Es la misma idea del original, con la diferencia
de que allá vivía dentro de una consulta SQL de treinta líneas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from gestvet.modules.appointments.domain.entities import Appointment
from gestvet.modules.appointments.domain.exceptions import (
    AppointmentTypeNotFound,
    NoEmergencyVeterinarian,
    PetNotOwned,
)
from gestvet.modules.appointments.ports.repositories import (
    AppointmentRepository,
    AppointmentTypeRepository,
    PetDirectory,
    ScheduleDirectory,
)


@dataclass(frozen=True, slots=True)
class OpenEmergencyCommand:
    client_id: int
    pet_id: int
    description: str = ""


class OpenEmergency:
    def __init__(
        self,
        appointments: AppointmentRepository,
        types: AppointmentTypeRepository,
        pets: PetDirectory,
        schedule: ScheduleDirectory,
    ) -> None:
        self._appointments = appointments
        self._types = types
        self._pets = pets
        self._schedule = schedule

    async def __call__(self, command: OpenEmergencyCommand) -> Appointment:
        emergency_type = await self._types.get_emergency()
        if emergency_type is None:
            raise AppointmentTypeNotFound(0)

        if not await self._pets.is_owned_by(command.pet_id, command.client_id):
            raise PetNotOwned(command.pet_id)

        now = datetime.now(UTC)
        veterinarian_id = await self._pick_veterinarian(now)

        return await self._appointments.add(
            Appointment(
                scheduled_at=now,
                duration=emergency_type.duration,
                client_id=command.client_id,
                pet_id=command.pet_id,
                veterinarian_id=veterinarian_id,
                appointment_type_id=emergency_type.id or 0,
                description=command.description or "Cita de emergencia",
            )
        )

    async def _pick_veterinarian(self, moment: datetime) -> int:
        on_duty = await self._schedule.veterinarians_on_duty(moment)
        if not on_duty:
            raise NoEmergencyVeterinarian()

        # Entre los de guardia gana el menos cargado. El original ordenaba por
        # la misma cuenta, pero además descartaba a cualquiera que tuviera una
        # cita activa, así que con la clínica llena no asignaba a nadie.
        loads = [(await self._appointments.count_active_for(vet_id), vet_id) for vet_id in on_duty]
        return min(loads)[1]

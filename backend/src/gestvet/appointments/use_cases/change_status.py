"""Caso de uso: mover una cita de estado.

Quién puede hacer qué es una regla de negocio y vive acá, no en el router.
El veterinario confirma y completa; el cliente solo cancela lo suyo; ambos
pueden cancelar una cita en la que participan.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.appointments.domain.entities import Appointment, AppointmentStatus
from gestvet.appointments.domain.exceptions import AppointmentNotFound, InvalidAppointment
from gestvet.appointments.ports.repositories import AppointmentRepository
from gestvet.core.identity import Role

# Confirmar y completar son actos clínicos: los hace quien atiende.
_CLINICAL_TRANSITIONS = frozenset({AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED})


@dataclass(frozen=True, slots=True)
class ChangeStatusCommand:
    appointment_id: int
    actor_id: int
    actor_role: Role
    target: AppointmentStatus
    reason: str = ""


class ChangeAppointmentStatus:
    def __init__(self, appointments: AppointmentRepository) -> None:
        self._appointments = appointments

    async def __call__(self, command: ChangeStatusCommand) -> Appointment:
        appointment = await self._appointments.get(command.appointment_id)
        if appointment is None or not self._may_see(appointment, command):
            # Una cita ajena no existe. Distinguir los dos casos revelaría que
            # ese identificador pertenece a alguien.
            raise AppointmentNotFound(command.appointment_id)

        self._require_authority(command)

        if command.target is AppointmentStatus.CANCELLED:
            appointment.cancel(command.actor_id, command.reason)
        elif command.target is AppointmentStatus.CONFIRMED:
            appointment.confirm(command.actor_id)
        else:
            appointment.complete(command.actor_id)

        return await self._appointments.save(appointment)

    @staticmethod
    def _may_see(appointment: Appointment, command: ChangeStatusCommand) -> bool:
        if command.actor_role is Role.ADMIN:
            return True
        return appointment.involves(command.actor_id)

    @staticmethod
    def _require_authority(command: ChangeStatusCommand) -> None:
        if command.target in _CLINICAL_TRANSITIONS and command.actor_role is Role.CLIENT:
            raise InvalidAppointment(
                "Confirmar o completar una cita le corresponde al veterinario."
            )

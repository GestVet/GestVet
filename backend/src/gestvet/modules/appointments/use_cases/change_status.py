"""Caso de uso: mover una cita de estado.

Quién puede hacer qué es una regla de negocio y vive acá, no en el router.
El veterinario confirma y completa; el cliente solo cancela lo suyo; ambos
pueden cancelar una cita en la que participan.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity import Role
from gestvet.modules.appointments.domain.entities import Appointment, AppointmentStatus
from gestvet.modules.appointments.domain.exceptions import AppointmentNotFound, InvalidAppointment
from gestvet.modules.appointments.ports.repositories import AppointmentRepository

# Confirmar, completar y marcar la inasistencia son actos clínicos: los hace
# quien atiende, nunca el cliente.
_CLINICAL_TRANSITIONS = frozenset(
    {AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW}
)

_ASIENTO_POR_ESTADO: dict[AppointmentStatus, ActivityKind] = {
    AppointmentStatus.CONFIRMED: ActivityKind.APPOINTMENT_CONFIRMED,
    AppointmentStatus.COMPLETED: ActivityKind.APPOINTMENT_COMPLETED,
    AppointmentStatus.CANCELLED: ActivityKind.APPOINTMENT_CANCELLED,
    AppointmentStatus.NO_SHOW: ActivityKind.APPOINTMENT_NO_SHOW,
}


@dataclass(frozen=True, slots=True)
class ChangeStatusCommand:
    appointment_id: int
    actor_id: int
    actor_role: Role
    target: AppointmentStatus
    reason: str = ""


class ChangeAppointmentStatus:
    def __init__(self, appointments: AppointmentRepository, activity: ActivityRecorder) -> None:
        self._appointments = appointments
        self._activity = activity

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
        elif command.target is AppointmentStatus.NO_SHOW:
            appointment.mark_no_show(command.actor_id)
        else:
            appointment.complete(command.actor_id)

        guardada = await self._appointments.save(appointment)
        await self._activity.record(
            command.actor_id, _ASIENTO_POR_ESTADO[command.target], appointment.cancellation_reason
        )
        return guardada

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

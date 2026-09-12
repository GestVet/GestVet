"""Caso de uso: presentar un reclamo sobre la atención de una cita."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.complaints.domain.entities import Complaint
from gestvet.modules.complaints.domain.exceptions import AppointmentNotFound
from gestvet.modules.complaints.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.complaints.ports.complaint_repository import ComplaintRepository


@dataclass(frozen=True, slots=True)
class FileComplaintCommand:
    appointment_id: int
    client_id: int
    description: str


class FileComplaint:
    def __init__(
        self,
        complaints: ComplaintRepository,
        appointments: AppointmentDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._complaints = complaints
        self._appointments = appointments
        self._activity = activity

    async def __call__(self, command: FileComplaintCommand) -> Complaint:
        details = await self._appointments.find_details(command.appointment_id)
        # Misma respuesta para "no existe" y "es de otro dueño": distinguirlas
        # confirmaría que el identificador pertenece a alguien.
        if details is None or details.client_id != command.client_id:
            raise AppointmentNotFound(command.appointment_id)

        complaint = Complaint(
            client_id=command.client_id,
            veterinarian_id=details.veterinarian_id,
            appointment_id=command.appointment_id,
            description=command.description,
        )
        guardado = await self._complaints.add(complaint)
        await self._activity.record(
            command.client_id,
            ActivityKind.COMPLAINT_FILED,
            f"Cita {guardado.appointment_id}, veterinario {guardado.veterinarian_id}",
        )
        return guardado

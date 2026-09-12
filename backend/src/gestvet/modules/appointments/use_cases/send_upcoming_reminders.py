"""Caso de uso: recordar por WhatsApp las citas confirmadas que se acercan.

Lo dispara un proceso periódico (ver `main.py`), no una petición HTTP: no hay
ningún actor humano detrás, así que no deja asiento en la bitácora de
movimientos, que registra lo que hace una cuenta.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from gestvet.core.whatsapp import WhatsAppSender
from gestvet.modules.appointments.domain.entities import Appointment
from gestvet.modules.appointments.ports.client_directory import ClientDirectory
from gestvet.modules.appointments.ports.repositories import AppointmentRepository, PetDirectory

# La ventana es de una hora y el proceso corre cada media hora (ver
# `main.py`), así que ninguna cita quedaria fuera de las dos pasadas que le
# tocan antes de que el margen termine de correrse.
REMINDER_LEAD_TIME = timedelta(hours=24)
REMINDER_WINDOW = timedelta(hours=1)


@dataclass(frozen=True, slots=True)
class ReminderResult:
    appointment_id: int
    notified: bool


class SendUpcomingReminders:
    def __init__(
        self,
        appointments: AppointmentRepository,
        clients: ClientDirectory,
        pets: PetDirectory,
        whatsapp: WhatsAppSender,
    ) -> None:
        self._appointments = appointments
        self._clients = clients
        self._pets = pets
        self._whatsapp = whatsapp

    async def __call__(self, now: datetime | None = None) -> list[ReminderResult]:
        moment = now or datetime.now(UTC)
        window_start = moment + REMINDER_LEAD_TIME
        window_end = window_start + REMINDER_WINDOW

        due = await self._appointments.find_due_for_reminder(window_start, window_end)
        return [await self._remind(appointment, moment) for appointment in due]

    async def _remind(self, appointment: Appointment, now: datetime) -> ReminderResult:
        contact = await self._clients.find_contact(appointment.client_id)
        notified = contact is not None and bool(contact.phone)
        if notified and contact is not None:
            pet_name = await self._pets.find_name(appointment.pet_id)
            await self._whatsapp.send_appointment_reminder(
                to=contact.phone,
                client_name=contact.name,
                pet_name=pet_name or "tu mascota",
                scheduled_at=appointment.scheduled_at,
            )

        # Se marca aunque no haya teléfono: reintentar en la próxima vuelta no
        # va a conseguir un número que no existe, y dejarla pendiente para
        # siempre satura la consulta de citas por recordar sin ningún beneficio.
        appointment.mark_reminder_sent(now)
        await self._appointments.save(appointment)
        return ReminderResult(appointment_id=appointment.id or 0, notified=notified)

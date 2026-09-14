"""Caso de uso: avisar por WhatsApp que a una mascota le toca una vacuna.

Lo dispara el mismo proceso periódico que recuerda las citas (ver `main.py`),
no una petición HTTP: no hay una cuenta detrás, así que no deja asiento en la
bitácora de movimientos.

Se avisa una sola vez por dosis, una semana antes, y solo por la última
aplicación de cada vacuna: si ya se puso un refuerzo, el vencimiento anterior
dejó de importar. Eso lo resuelve el repositorio.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from gestvet.core.clinic_time import CLINIC_UTC_OFFSET, clinic_date
from gestvet.core.whatsapp import WhatsAppSender
from gestvet.modules.medical_records.domain.vaccination import VACCINE_REMINDER_DAYS, Vaccination
from gestvet.modules.medical_records.ports.owner_contact_directory import OwnerContactDirectory
from gestvet.modules.medical_records.ports.vaccination_repository import VaccinationRepository

# Un aviso de vacuna no es urgente: sale en horario de atención, en la hora de
# la clínica, y no de madrugada. El proceso corre cada media hora, así que la
# primera vuelta de la mañana manda lo que se juntó durante la noche.
REMINDER_HOURS = range(9, 20)


@dataclass(frozen=True, slots=True)
class VaccineReminderResult:
    vaccination_id: int
    notified: bool


class SendVaccineReminders:
    def __init__(
        self,
        vaccinations: VaccinationRepository,
        contacts: OwnerContactDirectory,
        whatsapp: WhatsAppSender,
    ) -> None:
        self._vaccinations = vaccinations
        self._contacts = contacts
        self._whatsapp = whatsapp

    async def __call__(self, now: datetime | None = None) -> list[VaccineReminderResult]:
        moment = now or datetime.now(UTC)
        if (moment + CLINIC_UTC_OFFSET).hour not in REMINDER_HOURS:
            return []

        today = clinic_date(moment)
        due = await self._vaccinations.find_due_for_reminder(
            today, today + timedelta(days=VACCINE_REMINDER_DAYS)
        )
        return [await self._remind(vaccination, moment) for vaccination in due]

    async def _remind(self, vaccination: Vaccination, now: datetime) -> VaccineReminderResult:
        contact = await self._contacts.contact_for_pet(vaccination.pet_id)
        due_on = vaccination.next_due_on
        notified = contact is not None and bool(contact.phone) and due_on is not None
        if notified and contact is not None and due_on is not None:
            await self._whatsapp.send_vaccine_due_reminder(
                to=contact.phone,
                client_name=contact.owner_name,
                pet_name=contact.pet_name,
                vaccine_label=vaccination.label,
                due_on=due_on,
            )

        # Se marca aunque no haya a quién avisar, igual que en las citas: la
        # próxima vuelta no va a conseguir un teléfono que no existe.
        await self._vaccinations.mark_reminder_sent(vaccination.id or 0, now)
        return VaccineReminderResult(vaccination_id=vaccination.id or 0, notified=notified)

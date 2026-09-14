"""Adaptador de WhatsApp que registra los mensajes en el log.

Deja probar el flujo completo sin ninguna cuenta externa: cada mensaje queda en
el log estructurado del backend, con el número enmascarado. La hora se escribe
en la de la clínica, que es la que lee el cliente.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from gestvet.core.clinic_time import CLINIC_UTC_OFFSET
from gestvet.core.logs import get_logger

logger = get_logger("gestvet.whatsapp")

# Lo que queda visible de un número en el log: alcanza para reconocerlo.
_VISIBLE_DIGITS = 3


def _mask_phone(phone: str) -> str:
    digits = "".join(character for character in phone if character.isdigit())
    return f"***{digits[-_VISIBLE_DIGITS:]}" if digits else ""


class ConsoleWhatsAppSender:
    async def send_appointment_confirmed(
        self, *, to: str, client_name: str, pet_name: str, scheduled_at: datetime
    ) -> None:
        local = scheduled_at + CLINIC_UTC_OFFSET
        self._log(
            to,
            "appointment_confirmed",
            f"Hola {client_name}, la cita de {pet_name} quedó confirmada para el "
            f"{local:%d/%m} a las {local:%H:%M}.",
        )

    async def send_appointment_reminder(
        self, *, to: str, client_name: str, pet_name: str, scheduled_at: datetime
    ) -> None:
        local = scheduled_at + CLINIC_UTC_OFFSET
        self._log(
            to,
            "appointment_reminder",
            f"Hola {client_name}, te recordamos la cita de {pet_name} mañana "
            f"{local:%d/%m} a las {local:%H:%M}. Si no puedes asistir, cancélala desde la app.",
        )

    async def send_payment_confirmed(self, *, to: str, client_name: str, amount: Decimal) -> None:
        self._log(
            to, "payment_confirmed", f"Hola {client_name}, tu pago de S/ {amount} fue confirmado."
        )

    async def send_vaccine_due_reminder(
        self, *, to: str, client_name: str, pet_name: str, vaccine_label: str, due_on: date
    ) -> None:
        self._log(
            to,
            "vaccine_due_reminder",
            f"Hola {client_name}, a {pet_name} le toca {vaccine_label} el {due_on:%d/%m}. "
            "Reserva una cita desde la app para ponérsela a tiempo.",
        )

    @staticmethod
    def _log(to: str, template: str, message: str) -> None:
        logger.info("whatsapp.simulated", to=_mask_phone(to), template=template, message=message)

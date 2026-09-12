"""Notificaciones por WhatsApp.

De un solo sentido: el sistema le avisa al cliente, nunca al revés. Ningún
flujo depende de leer una respuesta, así que no hace falta nada de lenguaje
natural ni de IA para esto.

Vive en el núcleo porque lo usan varios módulos (citas, pagos) y no habla
ningún tipo de negocio: recibe un número, un nombre y los datos ya resueltos
para armar el texto. Cada módulo que lo necesita declara su propia
dependencia hacia este puerto, igual que hace `accounts` con `EmailSender`.

`ConsoleWhatsAppSender` es el único adaptador hoy: registra el mensaje en el
log en vez de mandarlo. El día que exista una cuenta de WhatsApp Business API
(directo con Meta, o vía un intermediario como Twilio), se reemplaza por un
adaptador que sí entregue el mensaje sin tocar ningún caso de uso: el puerto
no cambia. Ver `README.md` para el trámite pendiente de esa cuenta.

Quien llama a este puerto es responsable de no invocarlo con un número vacío:
un cliente sin teléfono cargado simplemente no recibe el mensaje, y eso lo
decide el caso de uso, no el adaptador.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol


class WhatsAppSender(Protocol):
    async def send_appointment_confirmed(
        self, *, to: str, client_name: str, pet_name: str, scheduled_at: datetime
    ) -> None: ...

    async def send_appointment_reminder(
        self, *, to: str, client_name: str, pet_name: str, scheduled_at: datetime
    ) -> None: ...

    async def send_payment_confirmed(
        self, *, to: str, client_name: str, amount: Decimal
    ) -> None: ...


class ConsoleWhatsAppSender:
    async def send_appointment_confirmed(
        self, *, to: str, client_name: str, pet_name: str, scheduled_at: datetime
    ) -> None:
        print(
            f"WhatsApp a {to}: Hola {client_name}, la cita de {pet_name} quedó "
            f"confirmada para el {scheduled_at:%d/%m} a las {scheduled_at:%H:%M}."
        )

    async def send_appointment_reminder(
        self, *, to: str, client_name: str, pet_name: str, scheduled_at: datetime
    ) -> None:
        print(
            f"WhatsApp a {to}: Hola {client_name}, te recordamos la cita de {pet_name} "
            f"mañana {scheduled_at:%d/%m} a las {scheduled_at:%H:%M}. "
            "Si no podés asistir, cancelala desde la app."
        )

    async def send_payment_confirmed(self, *, to: str, client_name: str, amount: Decimal) -> None:
        print(f"WhatsApp a {to}: Hola {client_name}, tu pago de S/ {amount} fue confirmado.")

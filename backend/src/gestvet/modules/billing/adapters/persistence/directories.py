"""Adaptador del lector hacia `appointments`.

Consulta cruda contra la tabla ajena, acotada a estas preguntas y cubierta
por pruebas, igual que hacen los demás lectores cruzados del proyecto.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.billing.ports.client_directory import ClientContact

_FIND_CLIENT_ID = text("SELECT client_id FROM appointments WHERE id = :appointment_id")

_CLIENT_CONTACT = text("SELECT first_name, last_name, phone FROM users WHERE id = :client_id")

_FIND_AMOUNT_DUE = text(
    "SELECT appointment_types.price FROM appointments "
    "JOIN appointment_types ON appointment_types.id = appointments.appointment_type_id "
    "WHERE appointments.id = :appointment_id"
)

_IS_COMPLETED = text(
    "SELECT 1 FROM appointments WHERE id = :appointment_id AND status = 'completed'"
)

_IS_EMERGENCY = text(
    "SELECT appointment_types.is_emergency FROM appointments "
    "JOIN appointment_types ON appointment_types.id = appointments.appointment_type_id "
    "WHERE appointments.id = :appointment_id"
)


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_client_id(self, appointment_id: int) -> int | None:
        row = (
            await self._session.execute(_FIND_CLIENT_ID, {"appointment_id": appointment_id})
        ).first()
        return int(row.client_id) if row else None

    async def find_amount_due(self, appointment_id: int) -> Decimal | None:
        row = (
            await self._session.execute(_FIND_AMOUNT_DUE, {"appointment_id": appointment_id})
        ).first()
        return Decimal(str(row.price)) if row else None

    async def is_completed(self, appointment_id: int) -> bool:
        row = (
            await self._session.execute(_IS_COMPLETED, {"appointment_id": appointment_id})
        ).first()
        return row is not None

    async def is_emergency(self, appointment_id: int) -> bool:
        row = (
            await self._session.execute(_IS_EMERGENCY, {"appointment_id": appointment_id})
        ).first()
        return bool(row.is_emergency) if row else False


class SqlClientDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_contact(self, client_id: int) -> ClientContact | None:
        row = (await self._session.execute(_CLIENT_CONTACT, {"client_id": client_id})).first()
        if row is None:
            return None
        return ClientContact(name=f"{row.first_name} {row.last_name}".strip(), phone=row.phone)

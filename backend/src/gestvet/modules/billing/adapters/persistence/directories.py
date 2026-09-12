"""Adaptador del lector hacia `appointments`.

Consulta cruda contra la tabla ajena, acotada a esta única pregunta y cubierta
por pruebas, igual que hacen los demás lectores cruzados del proyecto.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_FIND_CLIENT_ID = text("SELECT client_id FROM appointments WHERE id = :appointment_id")


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_client_id(self, appointment_id: int) -> int | None:
        row = (
            await self._session.execute(_FIND_CLIENT_ID, {"appointment_id": appointment_id})
        ).first()
        return int(row.client_id) if row else None

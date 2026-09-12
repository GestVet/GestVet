"""Adaptador del lector hacia `appointments`.

Consulta cruda contra la tabla ajena, acotada a esta única pregunta y
cubierta por pruebas, igual que hacen los demás lectores cruzados del
proyecto.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.complaints.ports.appointment_directory import AppointmentDetails

_FIND_DETAILS = text(
    "SELECT client_id, veterinarian_id FROM appointments WHERE id = :appointment_id"
)


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_details(self, appointment_id: int) -> AppointmentDetails | None:
        row = (
            await self._session.execute(_FIND_DETAILS, {"appointment_id": appointment_id})
        ).first()
        if row is None:
            return None
        return AppointmentDetails(
            client_id=int(row.client_id), veterinarian_id=int(row.veterinarian_id)
        )

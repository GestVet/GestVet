"""Adaptador del lector hacia `appointments`.

Consulta cruda contra la tabla ajena, acotada a esta única pregunta y
cubierta por pruebas, igual que hacen los demás lectores cruzados del
proyecto.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_HAS_COMPLETED_APPOINTMENT = text(
    "SELECT 1 FROM appointments "
    "WHERE client_id = :client_id AND veterinarian_id = :veterinarian_id "
    "AND status = 'completed' LIMIT 1"
)


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_completed_appointment(self, client_id: int, veterinarian_id: int) -> bool:
        row = (
            await self._session.execute(
                _HAS_COMPLETED_APPOINTMENT,
                {"client_id": client_id, "veterinarian_id": veterinarian_id},
            )
        ).first()
        return row is not None

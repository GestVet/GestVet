"""Adaptador del lector hacia `appointments`.

Consulta cruda contra la tabla ajena, acotada a esta única pregunta y cubierta
por pruebas, igual que hacen los lectores de `appointments` hacia `pets` y
`availability`.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Los estados activos de una cita están duplicados a mano porque el dominio de
# `appointments` no se puede importar desde acá. Son los mismos dos valores
# desde que existe el módulo: 'pending' y 'confirmed'.
_HAS_UPCOMING_NORMAL = text(
    "SELECT 1 FROM appointments a "
    "JOIN appointment_types t ON t.id = a.appointment_type_id "
    "WHERE a.veterinarian_id = :veterinarian_id "
    "AND a.status IN ('pending', 'confirmed') "
    "AND t.is_emergency = :is_emergency "
    "LIMIT 1"
)


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_upcoming_normal_appointments(self, veterinarian_id: int) -> bool:
        row = (
            await self._session.execute(
                _HAS_UPCOMING_NORMAL,
                {"veterinarian_id": veterinarian_id, "is_emergency": False},
            )
        ).first()
        return row is not None

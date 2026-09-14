"""Lectores hacia tablas de otros módulos: cuentas y citas.

Consultas escritas a mano, acotadas a la pregunta de cada puerto, igual que
hacen los lectores de `appointments` hacia `pets` y la agenda. Se lee, nunca se
escribe.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role

_MOMENT = DateTime(timezone=True)

_IS_ACTIVE_VETERINARIAN = text(
    "SELECT 1 FROM users WHERE id = :user_id AND role = :role AND is_active = :active"
)

# Los estados activos de una cita están escritos a mano porque el dominio de
# `appointments` no se puede importar desde acá: 'pending' y 'confirmed'.
_HAS_ACTIVE_APPOINTMENTS = text(
    "SELECT 1 FROM appointments "
    "WHERE veterinarian_id = :veterinarian_id "
    "AND status IN ('pending', 'confirmed') "
    "AND scheduled_at >= :starts_at AND scheduled_at < :ends_at "
    "LIMIT 1"
).bindparams(
    bindparam("starts_at", type_=_MOMENT),
    bindparam("ends_at", type_=_MOMENT),
)


class SqlVeterinarianDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def is_active_veterinarian(self, user_id: int) -> bool:
        row = (
            await self._session.execute(
                _IS_ACTIVE_VETERINARIAN,
                {"user_id": user_id, "role": Role.VETERINARIAN.value, "active": True},
            )
        ).first()
        return row is not None


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_active_appointments(
        self, veterinarian_id: int, starts_at: datetime, ends_at: datetime
    ) -> bool:
        row = (
            await self._session.execute(
                _HAS_ACTIVE_APPOINTMENTS,
                {"veterinarian_id": veterinarian_id, "starts_at": starts_at, "ends_at": ends_at},
            )
        ).first()
        return row is not None

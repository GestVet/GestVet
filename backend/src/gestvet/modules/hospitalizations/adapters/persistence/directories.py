"""Adaptadores de lectura hacia `appointments` y `pets`.

Consultas crudas contra tablas ajenas, igual que hacen los lectores de otros
módulos hacia esas mismas tablas.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_FIND_PET_ID = text("SELECT pet_id FROM appointments WHERE id = :appointment_id")

_PET_EXISTS = text("SELECT 1 FROM pets WHERE id = :pet_id")

_PET_IS_OWNED = text("SELECT 1 FROM pets WHERE id = :pet_id AND owner_id = :owner_id")


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_pet_id(self, appointment_id: int) -> int | None:
        row = (
            await self._session.execute(_FIND_PET_ID, {"appointment_id": appointment_id})
        ).first()
        return None if row is None else row[0]


class SqlPetDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists(self, pet_id: int) -> bool:
        row = (await self._session.execute(_PET_EXISTS, {"pet_id": pet_id})).first()
        return row is not None

    async def is_owned_by(self, pet_id: int, owner_id: int) -> bool:
        row = (
            await self._session.execute(_PET_IS_OWNED, {"pet_id": pet_id, "owner_id": owner_id})
        ).first()
        return row is not None

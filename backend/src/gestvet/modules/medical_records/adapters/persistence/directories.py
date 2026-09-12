"""Adaptador del lector hacia `pets`.

Consulta cruda contra la tabla ajena, acotada a estas dos preguntas y cubierta
por pruebas, igual que hacen los lectores de `appointments` hacia `pets` y
`availability`.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_PET_EXISTS = text("SELECT 1 FROM pets WHERE id = :pet_id")

_PET_IS_OWNED = text("SELECT 1 FROM pets WHERE id = :pet_id AND owner_id = :owner_id")


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

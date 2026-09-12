"""Adaptador del lector hacia `pets`.

Consulta cruda contra la tabla ajena, acotada a estas dos preguntas y cubierta
por pruebas, igual que hacen los lectores de `appointments` hacia `pets` y
`availability`.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.medical_records.ports.pet_directory import PetSummary

_PET_EXISTS = text("SELECT 1 FROM pets WHERE id = :pet_id")

_PET_IS_OWNED = text("SELECT 1 FROM pets WHERE id = :pet_id AND owner_id = :owner_id")

# El reporte necesita el nombre del dueño, que vive en `users`: sigue siendo
# una lectura cruda contra una tabla ajena, no una importación de código.
_PET_SUMMARY = text(
    "SELECT pets.name, pets.species, pets.breed, "
    "users.first_name, users.last_name "
    "FROM pets JOIN users ON users.id = pets.owner_id "
    "WHERE pets.id = :pet_id"
)


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

    async def summary(self, pet_id: int) -> PetSummary | None:
        row = (await self._session.execute(_PET_SUMMARY, {"pet_id": pet_id})).first()
        if row is None:
            return None
        name, species, breed, first_name, last_name = row
        return PetSummary(
            name=name,
            species=species,
            breed=breed,
            owner_name=f"{first_name} {last_name}".strip(),
        )

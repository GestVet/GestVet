"""Implementación del puerto `PetRepository` sobre SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.pagination import Page
from gestvet.modules.pets.adapters.persistence.mappers import entity_to_row, row_to_entity
from gestvet.modules.pets.adapters.persistence.models import PetRow
from gestvet.modules.pets.domain.entities import Pet
from gestvet.modules.pets.ports.pet_repository import PetQuery


class SqlAlchemyPetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, pet: Pet) -> Pet:
        row = entity_to_row(pet)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def get(self, pet_id: int, owner_id: int | None = None) -> Pet | None:
        statement = select(PetRow).where(PetRow.id == pet_id)
        if owner_id is not None:
            # La propiedad entra en la consulta, no en un `if` posterior.
            statement = statement.where(PetRow.owner_id == owner_id)
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return row_to_entity(row) if row else None

    async def save(self, pet: Pet) -> Pet:
        row = await self._session.get(PetRow, pet.id)
        if row is None:
            raise ValueError(f"La mascota {pet.id} ya no existe.")
        row.name = pet.name
        row.species = pet.species
        row.breed = pet.breed
        row.birth_date = pet.birth_date
        row.is_active = pet.is_active
        await self._session.flush()
        return row_to_entity(row)

    async def search(self, query: PetQuery) -> Page[Pet]:
        base = self._apply_filters(select(PetRow), query)

        total = int(
            (
                await self._session.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
        )
        rows = await self._session.execute(
            base.order_by(PetRow.name.asc(), PetRow.id).limit(query.limit).offset(query.offset)
        )
        return Page(items=[row_to_entity(row) for row in rows.scalars().all()], total=total)

    def _apply_filters(
        self, statement: Select[tuple[PetRow]], query: PetQuery
    ) -> Select[tuple[PetRow]]:
        if query.owner_id is not None:
            statement = statement.where(PetRow.owner_id == query.owner_id)
        if query.is_active is not None:
            statement = statement.where(PetRow.is_active == query.is_active)
        if query.search:
            pattern = f"%{query.search}%"
            statement = statement.where(
                or_(
                    PetRow.name.ilike(pattern),
                    PetRow.species.ilike(pattern),
                    PetRow.breed.ilike(pattern),
                )
            )
        return statement

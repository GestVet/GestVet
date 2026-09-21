from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.accounts.adapters.persistence.mappers import specialty_row_to_entity
from gestvet.modules.accounts.adapters.persistence.models import (
    SpecialtyRow,
    VeterinarianSpecialtyRow,
)
from gestvet.modules.accounts.domain.specialties import Specialty, specialty_key


class SqlAlchemySpecialtyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, *, include_inactive: bool) -> list[Specialty]:
        statement = select(SpecialtyRow).order_by(SpecialtyRow.category, SpecialtyRow.name_key)
        if not include_inactive:
            statement = statement.where(SpecialtyRow.is_active.is_(True))
        rows = (await self._session.execute(statement)).scalars().all()
        return [specialty_row_to_entity(row) for row in rows]

    async def get(self, specialty_id: int) -> Specialty | None:
        row = await self._session.get(SpecialtyRow, specialty_id)
        return specialty_row_to_entity(row) if row else None

    async def get_many(self, specialty_ids: frozenset[int]) -> list[Specialty]:
        if not specialty_ids:
            return []
        rows = await self._session.execute(
            select(SpecialtyRow).where(SpecialtyRow.id.in_(specialty_ids))
        )
        return [specialty_row_to_entity(row) for row in rows.scalars()]

    async def find_id(self, key: str) -> int | None:
        statement = select(SpecialtyRow.id).where(SpecialtyRow.name_key == key)
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def add(self, specialty: Specialty) -> Specialty:
        row = SpecialtyRow(
            name=specialty.name,
            name_key=specialty_key(specialty.name),
            category=specialty.category.value,
            description=specialty.description,
            is_active=specialty.is_active,
        )
        self._session.add(row)
        await self._session.flush()
        return specialty_row_to_entity(row)

    async def save(self, specialty: Specialty) -> Specialty:
        row = await self._session.get(SpecialtyRow, specialty.id)
        if row is None:
            raise ValueError(f"La especialidad {specialty.id} ya no existe.")
        row.name = specialty.name
        row.name_key = specialty_key(specialty.name)
        row.category = specialty.category.value
        row.description = specialty.description
        row.is_active = specialty.is_active
        await self._session.flush()
        return specialty_row_to_entity(row)

    async def specialties_for(self, user_ids: frozenset[int]) -> dict[int, list[Specialty]]:
        if not user_ids:
            return {}
        rows = await self._session.execute(
            select(VeterinarianSpecialtyRow.user_id, SpecialtyRow)
            .join(SpecialtyRow, SpecialtyRow.id == VeterinarianSpecialtyRow.specialty_id)
            .where(VeterinarianSpecialtyRow.user_id.in_(user_ids))
            .order_by(SpecialtyRow.category, SpecialtyRow.name_key)
        )
        by_user: dict[int, list[Specialty]] = {}
        for user_id, specialty_row in rows.all():
            by_user.setdefault(user_id, []).append(specialty_row_to_entity(specialty_row))
        return by_user

    async def assign(self, user_id: int, specialty_ids: frozenset[int]) -> None:
        await self._session.execute(
            delete(VeterinarianSpecialtyRow).where(VeterinarianSpecialtyRow.user_id == user_id)
        )
        self._session.add_all(
            [
                VeterinarianSpecialtyRow(user_id=user_id, specialty_id=specialty_id)
                for specialty_id in specialty_ids
            ]
        )
        await self._session.flush()

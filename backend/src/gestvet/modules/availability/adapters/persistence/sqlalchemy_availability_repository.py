"""Implementación del puerto `AvailabilityRepository` sobre SQLAlchemy."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.availability.adapters.persistence.mappers import entity_to_row, row_to_entity
from gestvet.modules.availability.adapters.persistence.models import AvailabilitySlotRow
from gestvet.modules.availability.domain.entities import AvailabilitySlot
from gestvet.modules.availability.ports.availability_repository import SlotQuery


class SqlAlchemyAvailabilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        row = entity_to_row(slot)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def get(
        self, slot_id: int, veterinarian_id: int | None = None
    ) -> AvailabilitySlot | None:
        statement = select(AvailabilitySlotRow).where(AvailabilitySlotRow.id == slot_id)
        if veterinarian_id is not None:
            statement = statement.where(AvailabilitySlotRow.veterinarian_id == veterinarian_id)
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return row_to_entity(row) if row else None

    async def list(self, query: SlotQuery) -> list[AvailabilitySlot]:
        statement = select(AvailabilitySlotRow)
        if query.veterinarian_id is not None:
            statement = statement.where(
                AvailabilitySlotRow.veterinarian_id == query.veterinarian_id
            )
        if query.starts_after is not None:
            statement = statement.where(AvailabilitySlotRow.ends_at > query.starts_after)
        if query.ends_before is not None:
            statement = statement.where(AvailabilitySlotRow.starts_at < query.ends_before)
        rows = await self._session.execute(statement.order_by(AvailabilitySlotRow.starts_at))
        return [row_to_entity(row) for row in rows.scalars().all()]

    async def find_overlapping(
        self, veterinarian_id: int, starts_at: datetime, ends_at: datetime
    ) -> list[AvailabilitySlot]:
        # Dos intervalos se cruzan si cada uno empieza antes de que el otro
        # termine. Compartir el extremo no cuenta, de ahí los `<` estrictos.
        rows = await self._session.execute(
            select(AvailabilitySlotRow).where(
                AvailabilitySlotRow.veterinarian_id == veterinarian_id,
                AvailabilitySlotRow.starts_at < ends_at,
                AvailabilitySlotRow.ends_at > starts_at,
            )
        )
        return [row_to_entity(row) for row in rows.scalars().all()]

    async def delete(self, slot_id: int, veterinarian_id: int) -> bool:
        result = await self._session.execute(
            delete(AvailabilitySlotRow).where(
                AvailabilitySlotRow.id == slot_id,
                AvailabilitySlotRow.veterinarian_id == veterinarian_id,
            )
        )
        await self._session.flush()
        return bool(result.rowcount)

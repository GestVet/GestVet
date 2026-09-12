from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.pagination import Page
from gestvet.modules.medical_records.adapters.persistence.mappers import (
    entity_to_row,
    row_to_entity,
)
from gestvet.modules.medical_records.adapters.persistence.models import ClinicalEntryRow
from gestvet.modules.medical_records.domain.entities import ClinicalEntry
from gestvet.modules.medical_records.ports.clinical_entry_repository import ClinicalEntryQuery


class SqlAlchemyClinicalEntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: ClinicalEntry) -> ClinicalEntry:
        row = entity_to_row(entry)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def search(self, query: ClinicalEntryQuery) -> Page[ClinicalEntry]:
        base = self._apply_filters(select(ClinicalEntryRow), query)

        total = int(
            (
                await self._session.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
        )
        rows = await self._session.execute(
            base.order_by(ClinicalEntryRow.occurred_at.desc(), ClinicalEntryRow.id.desc())
            .limit(query.limit)
            .offset(query.offset)
        )
        return Page(items=[row_to_entity(row) for row in rows.scalars().all()], total=total)

    def _apply_filters(
        self, statement: Select[tuple[ClinicalEntryRow]], query: ClinicalEntryQuery
    ) -> Select[tuple[ClinicalEntryRow]]:
        statement = statement.where(ClinicalEntryRow.pet_id == query.pet_id)
        if query.kind is not None:
            statement = statement.where(ClinicalEntryRow.kind == query.kind.value)
        return statement

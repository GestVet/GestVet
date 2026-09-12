from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.pagination import Page
from gestvet.modules.hospitalizations.adapters.persistence.mappers import (
    entity_to_row,
    note_entity_to_row,
    note_row_to_entity,
    row_to_entity,
)
from gestvet.modules.hospitalizations.adapters.persistence.models import (
    HospitalizationNoteRow,
    HospitalizationRow,
)
from gestvet.modules.hospitalizations.domain.entities import Hospitalization, HospitalizationNote
from gestvet.modules.hospitalizations.ports.hospitalization_repository import (
    HospitalizationQuery,
)


class SqlAlchemyHospitalizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, hospitalization: Hospitalization) -> Hospitalization:
        row = entity_to_row(hospitalization)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def get(self, hospitalization_id: int) -> Hospitalization | None:
        row = await self._session.get(HospitalizationRow, hospitalization_id)
        return row_to_entity(row) if row is not None else None

    async def save(self, hospitalization: Hospitalization) -> Hospitalization:
        row = await self._session.get(HospitalizationRow, hospitalization.id)
        if row is None:
            raise ValueError(f"La internación {hospitalization.id} ya no existe.")
        row.status = hospitalization.status.value
        row.discharge_notes = hospitalization.discharge_notes
        row.discharged_at = hospitalization.discharged_at
        await self._session.flush()
        return row_to_entity(row)

    async def search(self, query: HospitalizationQuery) -> Page[Hospitalization]:
        base = select(HospitalizationRow).where(HospitalizationRow.pet_id == query.pet_id)

        total = int(
            (
                await self._session.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
        )
        rows = await self._session.execute(
            base.order_by(HospitalizationRow.admitted_at.desc(), HospitalizationRow.id.desc())
            .limit(query.limit)
            .offset(query.offset)
        )
        return Page(items=[row_to_entity(row) for row in rows.scalars().all()], total=total)


class SqlAlchemyNoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, note: HospitalizationNote) -> HospitalizationNote:
        row = note_entity_to_row(note)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return note_row_to_entity(row)

    async def list_for_hospitalization(self, hospitalization_id: int) -> list[HospitalizationNote]:
        rows = await self._session.execute(
            select(HospitalizationNoteRow)
            .where(HospitalizationNoteRow.hospitalization_id == hospitalization_id)
            .order_by(HospitalizationNoteRow.created_at.asc(), HospitalizationNoteRow.id.asc())
        )
        return [note_row_to_entity(row) for row in rows.scalars().all()]

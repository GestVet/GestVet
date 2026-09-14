from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.pagination import Page
from gestvet.modules.medical_records.adapters.persistence.mappers import (
    attachment_entity_to_row,
    attachment_row_to_entity,
    entity_to_row,
    row_to_entity,
)
from gestvet.modules.medical_records.adapters.persistence.models import (
    AttachmentRow,
    ClinicalEntryRow,
    PetVaccinationRow,
)
from gestvet.modules.medical_records.domain.attachment import Attachment
from gestvet.modules.medical_records.domain.entities import ClinicalEntry
from gestvet.modules.medical_records.domain.vaccination import Vaccination, VaccineCode
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

    async def get(self, entry_id: int) -> ClinicalEntry | None:
        row = await self._session.get(ClinicalEntryRow, entry_id)
        return row_to_entity(row) if row is not None else None

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

    async def list_all_for_pet(self, pet_id: int) -> list[ClinicalEntry]:
        rows = await self._session.execute(
            select(ClinicalEntryRow)
            .where(ClinicalEntryRow.pet_id == pet_id)
            .order_by(ClinicalEntryRow.occurred_at.asc(), ClinicalEntryRow.id.asc())
        )
        return [row_to_entity(row) for row in rows.scalars().all()]

    def _apply_filters(
        self, statement: Select[tuple[ClinicalEntryRow]], query: ClinicalEntryQuery
    ) -> Select[tuple[ClinicalEntryRow]]:
        statement = statement.where(ClinicalEntryRow.pet_id == query.pet_id)
        if query.kind is not None:
            statement = statement.where(ClinicalEntryRow.kind == query.kind.value)
        return statement


class SqlAlchemyAttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, attachment: Attachment) -> Attachment:
        row = attachment_entity_to_row(attachment)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return attachment_row_to_entity(row)

    async def get(self, attachment_id: int) -> Attachment | None:
        row = await self._session.get(AttachmentRow, attachment_id)
        return attachment_row_to_entity(row) if row is not None else None

    async def list_for_entry(self, clinical_entry_id: int) -> list[Attachment]:
        rows = await self._session.execute(
            select(AttachmentRow)
            .where(AttachmentRow.clinical_entry_id == clinical_entry_id)
            .order_by(AttachmentRow.created_at.asc(), AttachmentRow.id.asc())
        )
        return [attachment_row_to_entity(row) for row in rows.scalars().all()]

    async def delete(self, attachment_id: int) -> None:
        row = await self._session.get(AttachmentRow, attachment_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()


def _vaccination(row: PetVaccinationRow) -> Vaccination:
    return Vaccination(
        id=row.id,
        pet_id=row.pet_id,
        veterinarian_id=row.veterinarian_id,
        appointment_id=row.appointment_id,
        vaccine=VaccineCode(row.vaccine),
        applied_on=row.applied_on,
        next_due_on=row.next_due_on,
        product_name=row.product_name,
        batch=row.batch,
        notes=row.notes,
        created_at=row.created_at,
    )


class SqlAlchemyVaccinationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, vaccination: Vaccination) -> Vaccination:
        row = PetVaccinationRow(
            pet_id=vaccination.pet_id,
            veterinarian_id=vaccination.veterinarian_id,
            appointment_id=vaccination.appointment_id,
            vaccine=vaccination.vaccine.value,
            applied_on=vaccination.applied_on,
            next_due_on=vaccination.next_due_on,
            product_name=vaccination.product_name,
            batch=vaccination.batch,
            notes=vaccination.notes,
            created_at=vaccination.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _vaccination(row)

    async def list_for_pet(self, pet_id: int) -> list[Vaccination]:
        rows = await self._session.execute(
            select(PetVaccinationRow)
            .where(PetVaccinationRow.pet_id == pet_id)
            .order_by(PetVaccinationRow.applied_on.desc(), PetVaccinationRow.id.desc())
        )
        return [_vaccination(row) for row in rows.scalars().all()]

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.pagination import Page
from gestvet.modules.complaints.adapters.persistence.mappers import (
    entity_to_row,
    evidence_entity_to_row,
    evidence_row_to_entity,
    row_to_entity,
)
from gestvet.modules.complaints.adapters.persistence.models import (
    ComplaintEvidenceRow,
    ComplaintRow,
)
from gestvet.modules.complaints.domain.entities import Complaint
from gestvet.modules.complaints.domain.evidence import ComplaintEvidence
from gestvet.modules.complaints.ports.complaint_repository import ComplaintQuery


class SqlAlchemyComplaintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, complaint: Complaint) -> Complaint:
        row = entity_to_row(complaint)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def get(self, complaint_id: int) -> Complaint | None:
        row = await self._session.get(ComplaintRow, complaint_id)
        return row_to_entity(row) if row else None

    async def search(self, query: ComplaintQuery) -> Page[Complaint]:
        base = self._apply_filters(select(ComplaintRow), query)

        total = int(
            (
                await self._session.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
        )
        rows = await self._session.execute(
            base.order_by(ComplaintRow.created_at.desc(), ComplaintRow.id.desc())
            .limit(query.limit)
            .offset(query.offset)
        )
        return Page(items=[row_to_entity(row) for row in rows.scalars().all()], total=total)

    def _apply_filters(
        self, statement: Select[tuple[ComplaintRow]], query: ComplaintQuery
    ) -> Select[tuple[ComplaintRow]]:
        if query.client_id is not None:
            statement = statement.where(ComplaintRow.client_id == query.client_id)
        if query.veterinarian_id is not None:
            statement = statement.where(ComplaintRow.veterinarian_id == query.veterinarian_id)
        return statement


class SqlAlchemyEvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, evidence: ComplaintEvidence) -> ComplaintEvidence:
        row = evidence_entity_to_row(evidence)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return evidence_row_to_entity(row)

    async def get(self, evidence_id: int) -> ComplaintEvidence | None:
        row = await self._session.get(ComplaintEvidenceRow, evidence_id)
        return evidence_row_to_entity(row) if row else None

    async def list_for_complaint(self, complaint_id: int) -> list[ComplaintEvidence]:
        rows = await self._session.execute(
            select(ComplaintEvidenceRow)
            .where(ComplaintEvidenceRow.complaint_id == complaint_id)
            .order_by(ComplaintEvidenceRow.created_at.asc(), ComplaintEvidenceRow.id.asc())
        )
        return [evidence_row_to_entity(row) for row in rows.scalars().all()]

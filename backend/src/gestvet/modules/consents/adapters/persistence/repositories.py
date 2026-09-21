from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.consents.adapters.persistence.mappers import (
    decision_columns,
    entity_to_row,
    row_to_entity,
    template_row_to_entity,
)
from gestvet.modules.consents.adapters.persistence.models import ConsentRow, ConsentTemplateRow
from gestvet.modules.consents.domain.entities import Consent, ConsentKind, ConsentTemplate
from gestvet.modules.consents.domain.exceptions import ConsentNotFound

# Un cliente acumula unos pocos pedidos por tratamiento; el tope evita que
# una cuenta con años de historia traiga todo de una vez.
_CLIENT_HISTORY_LIMIT = 200


class SqlAlchemyConsentTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, template_id: int) -> ConsentTemplate | None:
        row = await self._session.get(ConsentTemplateRow, template_id)
        return template_row_to_entity(row) if row else None

    async def current(self, kind: ConsentKind) -> ConsentTemplate | None:
        rows = await self._session.execute(
            select(ConsentTemplateRow)
            .where(
                ConsentTemplateRow.kind == kind.value,
                ConsentTemplateRow.is_active.is_(True),
            )
            .order_by(ConsentTemplateRow.version.desc())
            .limit(1)
        )
        row = rows.scalar_one_or_none()
        return template_row_to_entity(row) if row else None


class SqlAlchemyConsentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, consent: Consent) -> Consent:
        row = entity_to_row(consent)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def get(self, consent_id: int) -> Consent | None:
        row = await self._session.get(ConsentRow, consent_id)
        return row_to_entity(row) if row else None

    async def update(self, consent: Consent) -> Consent:
        row = await self._session.get(ConsentRow, consent.id) if consent.id else None
        if row is None:
            raise ConsentNotFound(consent.id or 0)
        for column, value in decision_columns(consent).items():
            setattr(row, column, value)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def list_for_appointment(self, appointment_id: int) -> list[Consent]:
        rows = await self._session.scalars(
            select(ConsentRow)
            .where(ConsentRow.appointment_id == appointment_id)
            .order_by(ConsentRow.created_at.desc(), ConsentRow.id.desc())
        )
        return [row_to_entity(row) for row in rows]

    async def list_for_client(self, client_id: int) -> list[Consent]:
        rows = await self._session.scalars(
            select(ConsentRow)
            .where(
                ConsentRow.client_id == client_id,
                ConsentRow.appointment_id.is_not(None),
            )
            .order_by(ConsentRow.created_at.desc(), ConsentRow.id.desc())
            .limit(_CLIENT_HISTORY_LIMIT)
        )
        return [row_to_entity(row) for row in rows]

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.availability.adapters.persistence.mappers import (
    entity_to_row,
    request_entity_to_row,
    request_row_to_entity,
    row_to_entity,
)
from gestvet.modules.availability.adapters.persistence.models import (
    AvailabilitySlotRow,
    ShiftChangeRequestRow,
)
from gestvet.modules.availability.domain.entities import AvailabilitySlot, ShiftChangeRequest
from gestvet.modules.availability.ports.availability_repository import (
    ChangeRequestQuery,
    SlotQuery,
)

# Un listado de pedidos sin paginar tiene que tener techo. Doscientos cubren
# meses de pedidos de un equipo chico.
_MAX_REQUESTS = 200


class SqlAlchemyAvailabilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        row = entity_to_row(slot)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def add_many(self, slots: list[AvailabilitySlot]) -> list[AvailabilitySlot]:
        rows = [entity_to_row(slot) for slot in slots]
        self._session.add_all(rows)
        await self._session.flush()
        return [row_to_entity(row) for row in rows]

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

    async def delete(self, slot_id: int) -> bool:
        result = await self._session.execute(
            delete(AvailabilitySlotRow).where(AvailabilitySlotRow.id == slot_id)
        )
        await self._session.flush()
        return bool(result.rowcount)


class SqlAlchemyShiftChangeRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, request: ShiftChangeRequest) -> ShiftChangeRequest:
        row = request_entity_to_row(request)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return request_row_to_entity(row)

    async def get(self, request_id: int) -> ShiftChangeRequest | None:
        row = await self._session.get(ShiftChangeRequestRow, request_id)
        return request_row_to_entity(row) if row else None

    async def save(self, request: ShiftChangeRequest) -> ShiftChangeRequest:
        row = await self._session.get(ShiftChangeRequestRow, request.id)
        if row is None:
            raise ValueError(f"El pedido {request.id} ya no existe.")
        row.status = request.status.value
        row.response = request.response
        row.resolved_by_id = request.resolved_by
        row.resolved_at = request.resolved_at
        await self._session.flush()
        return request_row_to_entity(row)

    async def list(self, query: ChangeRequestQuery) -> list[ShiftChangeRequest]:
        statement = select(ShiftChangeRequestRow)
        if query.veterinarian_id is not None:
            statement = statement.where(
                ShiftChangeRequestRow.veterinarian_id == query.veterinarian_id
            )
        if query.status is not None:
            statement = statement.where(ShiftChangeRequestRow.status == query.status.value)
        statement = statement.order_by(
            ShiftChangeRequestRow.created_at.desc(), ShiftChangeRequestRow.id.desc()
        ).limit(_MAX_REQUESTS)
        rows = await self._session.execute(statement)
        return [request_row_to_entity(row) for row in rows.scalars().all()]

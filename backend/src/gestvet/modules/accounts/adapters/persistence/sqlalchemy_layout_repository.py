"""Adaptador de persistencia con SQLAlchemy para preferencias de interfaz.

Implementa el puerto `LayoutRepository` mapeando entre las filas de la tabla
`user_layout_preferences` y las entidades del dominio de cuentas.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.accounts.adapters.persistence.mappers import layout_row_to_entity
from gestvet.modules.accounts.adapters.persistence.models import UserLayoutPreferenceRow
from gestvet.modules.accounts.domain.entities import UserLayoutPreference


class SqlAlchemyLayoutRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> UserLayoutPreference | None:
        row = await self._session.get(UserLayoutPreferenceRow, user_id)
        return layout_row_to_entity(row) if row is not None else None

    async def save(self, preference: UserLayoutPreference) -> UserLayoutPreference:
        row = await self._session.get(UserLayoutPreferenceRow, preference.user_id)
        now = datetime.now(UTC)
        blocks_data = [{"id": b.id, "visible": b.visible} for b in preference.dashboard_blocks]
        sidebar_data = list(preference.sidebar_order)

        if row is None:
            row = UserLayoutPreferenceRow(
                user_id=preference.user_id,
                sidebar_order=sidebar_data,
                dashboard_blocks=blocks_data,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row.sidebar_order = sidebar_data
            row.dashboard_blocks = blocks_data
            row.updated_at = now

        await self._session.flush()
        await self._session.refresh(row)
        return layout_row_to_entity(row)

    async def delete_by_user_id(self, user_id: int) -> None:
        row = await self._session.get(UserLayoutPreferenceRow, user_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()

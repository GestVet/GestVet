from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.accounts.adapters.persistence.mappers import (
    reset_token_entity_to_row,
    reset_token_row_to_entity,
)
from gestvet.modules.accounts.adapters.persistence.models import PasswordResetTokenRow
from gestvet.modules.accounts.domain.entities import PasswordResetToken


class SqlAlchemyPasswordResetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: PasswordResetToken) -> PasswordResetToken:
        row = reset_token_entity_to_row(token)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return reset_token_row_to_entity(row)

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        result = await self._session.execute(
            select(PasswordResetTokenRow).where(PasswordResetTokenRow.token_hash == token_hash)
        )
        row = result.scalar_one_or_none()
        return reset_token_row_to_entity(row) if row else None

    async def save(self, token: PasswordResetToken) -> PasswordResetToken:
        row = await self._session.get(PasswordResetTokenRow, token.id)
        if row is None:
            raise ValueError(f"El enlace {token.id} ya no existe.")
        row.used_at = token.used_at
        await self._session.flush()
        return reset_token_row_to_entity(row)

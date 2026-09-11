from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import DateTime, ForeignKey, Index, Select, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.activity import (
    MAX_DETAIL_LENGTH,
    ActivityKind,
    ActivityQuery,
    ActivityReader,
    ActivityRecord,
    ActivityRecorder,
)
from gestvet.core.database import Base, get_session
from gestvet.core.pagination import Page
from gestvet.core.timestamps import as_utc


class ActivityRow(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_activity_user", ondelete="RESTRICT"), index=True
    )
    kind: Mapped[str] = mapped_column(String(40), index=True)
    detail: Mapped[str] = mapped_column(String(MAX_DETAIL_LENGTH), default="")
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # La pantalla siempre pide los ultimos movimientos, y casi siempre de un
    # conjunto acotado de cuentas.
    __table_args__ = (Index("ix_activity_user_moment", "user_id", "occurred_at"),)


def _to_entity(row: ActivityRow) -> ActivityRecord:
    return ActivityRecord(
        id=row.id,
        user_id=row.user_id,
        kind=ActivityKind(row.kind),
        detail=row.detail,
        occurred_at=as_utc(row.occurred_at),
    )


class SqlActivityLog:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, user_id: int, kind: ActivityKind, detail: str = "") -> None:
        entrada = ActivityRecord(user_id=user_id, kind=kind, detail=detail)
        self._session.add(
            ActivityRow(
                user_id=entrada.user_id,
                kind=entrada.kind.value,
                detail=entrada.detail,
                occurred_at=entrada.occurred_at,
            )
        )
        await self._session.flush()

    async def search(self, query: ActivityQuery) -> Page[ActivityRecord]:
        base = self._apply_filters(select(ActivityRow), query)

        total = int(
            (
                await self._session.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
        )
        filas = await self._session.execute(
            base.order_by(ActivityRow.occurred_at.desc(), ActivityRow.id.desc())
            .limit(query.limit)
            .offset(query.offset)
        )
        return Page(items=[_to_entity(fila) for fila in filas.scalars().all()], total=total)

    def _apply_filters(
        self, statement: Select[tuple[ActivityRow]], query: ActivityQuery
    ) -> Select[tuple[ActivityRow]]:
        if query.user_ids is not None:
            statement = statement.where(ActivityRow.user_id.in_(query.user_ids))
        if query.kinds:
            statement = statement.where(ActivityRow.kind.in_([kind.value for kind in query.kinds]))
        if query.since is not None:
            statement = statement.where(ActivityRow.occurred_at >= query.since)
        if query.until is not None:
            statement = statement.where(ActivityRow.occurred_at < query.until)
        return statement


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_activity_recorder(session: SessionDep) -> ActivityRecorder:
    return SqlActivityLog(session)


def get_activity_reader(session: SessionDep) -> ActivityReader:
    return SqlActivityLog(session)


ActivityRecorderDep = Annotated[ActivityRecorder, Depends(get_activity_recorder)]
ActivityReaderDep = Annotated[ActivityReader, Depends(get_activity_reader)]

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from gestvet.core.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa compartida por los modelos de persistencia.

    Vive en el núcleo para que Alembic vea un único metadata, pero ninguna capa
    de dominio la importa: los contratos de Import Linter lo prohíben.
    """


_settings = get_settings()

engine = create_async_engine(_settings.database_url, echo=False, future=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

"""Pruebas del adaptador de persistencia SQLAlchemy para preferencias de interfaz."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.accounts.adapters.persistence.models import UserLayoutPreferenceRow
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_layout_repository import (
    SqlAlchemyLayoutRepository,
)
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import (
    DashboardBlockPreference,
    LayoutPreferences,
    UserLayoutPreference,
)
from tests.conftest import build_user


async def test_sqlalchemy_layout_repository_get_inexistente(session: AsyncSession) -> None:
    repo = SqlAlchemyLayoutRepository(session)
    resultado = await repo.get_by_user_id(999)
    assert resultado is None


async def test_sqlalchemy_layout_repository_save_nuevo_y_recuperar(session: AsyncSession) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("layout_repo@example.com"))
    await session.commit()

    repo = SqlAlchemyLayoutRepository(session)
    pref = UserLayoutPreference(
        user_id=user.id,  # type: ignore[arg-type]
        preferences=LayoutPreferences(
            sidebar_order=("/panel", "/mascotas"),
            dashboard_blocks=(
                DashboardBlockPreference(id="/panel/resumen", visible=True),
                DashboardBlockPreference(id="/panel/stats", visible=False),
            ),
            updated_at=datetime.now(UTC),
        ),
    )

    guardado = await repo.save(pref)
    assert guardado.user_id == user.id
    assert guardado.sidebar_order == ("/panel", "/mascotas")
    assert len(guardado.dashboard_blocks) == 2
    assert guardado.dashboard_blocks[0].id == "/panel/resumen"
    assert guardado.dashboard_blocks[0].visible is True
    assert guardado.dashboard_blocks[1].id == "/panel/stats"
    assert guardado.dashboard_blocks[1].visible is False
    assert guardado.updated_at is not None

    recuperado = await repo.get_by_user_id(user.id)  # type: ignore[arg-type]
    assert recuperado is not None
    assert recuperado.sidebar_order == ("/panel", "/mascotas")
    assert len(recuperado.dashboard_blocks) == 2


async def test_sqlalchemy_layout_repository_actualizar_upsert(session: AsyncSession) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("layout_upsert@example.com"))
    await session.commit()

    repo = SqlAlchemyLayoutRepository(session)
    pref1 = UserLayoutPreference(
        user_id=user.id,  # type: ignore[arg-type]
        preferences=LayoutPreferences(
            sidebar_order=("/panel",),
            dashboard_blocks=(),
            updated_at=datetime.now(UTC),
        ),
    )
    await repo.save(pref1)

    pref2 = UserLayoutPreference(
        user_id=user.id,  # type: ignore[arg-type]
        preferences=LayoutPreferences(
            sidebar_order=("/citas", "/panel"),
            dashboard_blocks=(DashboardBlockPreference(id="/citas/hoy"),),
            updated_at=datetime.now(UTC),
        ),
    )
    actualizado = await repo.save(pref2)
    assert actualizado.sidebar_order == ("/citas", "/panel")
    assert len(actualizado.dashboard_blocks) == 1

    recuperado = await repo.get_by_user_id(user.id)  # type: ignore[arg-type]
    assert recuperado is not None
    assert recuperado.sidebar_order == ("/citas", "/panel")


async def test_sqlalchemy_layout_repository_delete(session: AsyncSession) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("layout_del@example.com"))
    await session.commit()

    repo = SqlAlchemyLayoutRepository(session)
    await repo.save(
        UserLayoutPreference(
            user_id=user.id,  # type: ignore[arg-type]
            preferences=LayoutPreferences(
                sidebar_order=("/panel",),
                dashboard_blocks=(),
                updated_at=datetime.now(UTC),
            ),
        )
    )

    await repo.delete_by_user_id(user.id)  # type: ignore[arg-type]
    recuperado = await repo.get_by_user_id(user.id)  # type: ignore[arg-type]
    assert recuperado is None

    # Idempotente
    await repo.delete_by_user_id(user.id)  # type: ignore[arg-type]


def test_modelo_tabla_foreign_key_on_delete_cascade() -> None:
    """Verifica que la clave foránea esté configurada con ON DELETE CASCADE."""
    table = UserLayoutPreferenceRow.__table__
    fk = next(iter(table.foreign_keys))
    assert fk.column.table.name == "users"
    assert fk.column.name == "id"
    assert fk.ondelete == "CASCADE"

"""Pruebas de los casos de uso de preferencias de interfaz."""

from __future__ import annotations

import pytest

from gestvet.modules.accounts.domain.entities import (
    DashboardBlockPreference,
    LayoutPreferences,
    UserLayoutPreference,
)
from gestvet.modules.accounts.domain.exceptions import (
    DuplicateLayoutIdentifier,
    InvalidLayoutIdentifier,
    LayoutLimitExceeded,
)
from gestvet.modules.accounts.ports.layout_repository import LayoutRepository
from gestvet.modules.accounts.use_cases.manage_layout import (
    GetLayoutPreferences,
    ResetLayoutPreferences,
    SaveLayoutPreferences,
    SaveLayoutPreferencesCommand,
)


class InMemoryLayoutRepository(LayoutRepository):
    def __init__(self) -> None:
        self.store: dict[int, UserLayoutPreference] = {}

    async def get_by_user_id(self, user_id: int) -> UserLayoutPreference | None:
        return self.store.get(user_id)

    async def save(self, preference: UserLayoutPreference) -> UserLayoutPreference:
        self.store[preference.user_id] = preference
        return preference

    async def delete_by_user_id(self, user_id: int) -> None:
        self.store.pop(user_id, None)


async def test_get_layout_retorna_vacio_si_usuario_nunca_guardo() -> None:
    repo = InMemoryLayoutRepository()
    get_uc = GetLayoutPreferences(repo)

    resultado = await get_uc(user_id=1)

    assert resultado == LayoutPreferences.empty()
    assert resultado.sidebar_order == ()
    assert resultado.dashboard_blocks == ()
    assert resultado.updated_at is None


async def test_save_layout_guarda_y_retorna_preferencias() -> None:
    repo = InMemoryLayoutRepository()
    save_uc = SaveLayoutPreferences(repo)
    get_uc = GetLayoutPreferences(repo)

    cmd = SaveLayoutPreferencesCommand(
        user_id=10,
        sidebar_order=["/panel", "/mascotas"],
        dashboard_blocks=[
            DashboardBlockPreference(id="/panel/citas", visible=True),
            {"id": "/panel/stats", "visible": False},
        ],
    )
    guardado = await save_uc(cmd)

    assert guardado.sidebar_order == ("/panel", "/mascotas")
    assert len(guardado.dashboard_blocks) == 2
    assert guardado.dashboard_blocks[0].id == "/panel/citas"
    assert guardado.dashboard_blocks[0].visible is True
    assert guardado.dashboard_blocks[1].id == "/panel/stats"
    assert guardado.dashboard_blocks[1].visible is False
    assert guardado.updated_at is not None

    recuperado = await get_uc(user_id=10)
    assert recuperado.sidebar_order == guardado.sidebar_order
    assert recuperado.dashboard_blocks == guardado.dashboard_blocks
    assert recuperado.updated_at == guardado.updated_at


async def test_save_layout_actualiza_existente_upsert() -> None:
    repo = InMemoryLayoutRepository()
    save_uc = SaveLayoutPreferences(repo)
    get_uc = GetLayoutPreferences(repo)

    await save_uc(
        SaveLayoutPreferencesCommand(
            user_id=5,
            sidebar_order=["/panel"],
            dashboard_blocks=[{"id": "/b1", "visible": True}],
        )
    )

    actualizado = await save_uc(
        SaveLayoutPreferencesCommand(
            user_id=5,
            sidebar_order=["/citas", "/panel"],
            dashboard_blocks=[{"id": "/b2", "visible": False}],
        )
    )

    assert actualizado.sidebar_order == ("/citas", "/panel")
    assert len(actualizado.dashboard_blocks) == 1
    assert actualizado.dashboard_blocks[0].id == "/b2"

    recuperado = await get_uc(user_id=5)
    assert recuperado.sidebar_order == ("/citas", "/panel")


async def test_reset_layout_elimina_preferencias() -> None:
    repo = InMemoryLayoutRepository()
    save_uc = SaveLayoutPreferences(repo)
    get_uc = GetLayoutPreferences(repo)
    reset_uc = ResetLayoutPreferences(repo)

    await save_uc(
        SaveLayoutPreferencesCommand(
            user_id=7,
            sidebar_order=["/panel"],
            dashboard_blocks=[],
        )
    )

    await reset_uc(user_id=7)

    resultado = await get_uc(user_id=7)
    assert resultado == LayoutPreferences.empty()


async def test_reset_layout_es_idempotente() -> None:
    repo = InMemoryLayoutRepository()
    reset_uc = ResetLayoutPreferences(repo)

    await reset_uc(user_id=99)
    # No produce excepción al eliminar un registro inexistente


async def test_save_layout_rechaza_duplicados_y_patrones_invalidos() -> None:
    repo = InMemoryLayoutRepository()
    save_uc = SaveLayoutPreferences(repo)

    with pytest.raises(DuplicateLayoutIdentifier):
        await save_uc(
            SaveLayoutPreferencesCommand(
                user_id=1,
                sidebar_order=["/panel", "/panel"],
                dashboard_blocks=[],
            )
        )

    with pytest.raises(InvalidLayoutIdentifier):
        await save_uc(
            SaveLayoutPreferencesCommand(
                user_id=1,
                sidebar_order=["/RutaInvalida"],
                dashboard_blocks=[],
            )
        )

    with pytest.raises(LayoutLimitExceeded):
        await save_uc(
            SaveLayoutPreferencesCommand(
                user_id=1,
                sidebar_order=[f"/r/{i}" for i in range(51)],
                dashboard_blocks=[],
            )
        )

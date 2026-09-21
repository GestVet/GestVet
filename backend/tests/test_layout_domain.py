"""Pruebas del dominio para las preferencias de interfaz (sidebar y dashboard)."""

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
    InvalidLayoutPreferences,
    LayoutLimitExceeded,
)


def test_dashboard_block_preference_valida() -> None:
    bloque = DashboardBlockPreference(id="/panel", visible=True)
    assert bloque.id == "/panel"
    assert bloque.visible is True

    bloque_oculto = DashboardBlockPreference(id="citas_hoy", visible=False)
    assert bloque_oculto.id == "citas_hoy"
    assert bloque_oculto.visible is False

    bloque_complejo = DashboardBlockPreference(id="a/b-c_123")
    assert bloque_complejo.id == "a/b-c_123"
    assert bloque_complejo.visible is True


@pytest.mark.parametrize(
    "id_invalido",
    [
        "",
        "a" * 65,
        "/Panel",
        "panel con espacios",
        "/panel/1@2",
        "panel#1",
        "ruta?param=1",
        "/citas/nueva!",
    ],
)
def test_dashboard_block_preference_id_invalido(id_invalido: str) -> None:
    with pytest.raises(InvalidLayoutIdentifier):
        DashboardBlockPreference(id=id_invalido)


def test_dashboard_block_preference_visible_invalido() -> None:
    with pytest.raises(InvalidLayoutPreferences):
        DashboardBlockPreference(id="/panel", visible="si")  # type: ignore[arg-type]


def test_layout_preferences_vacio_por_defecto() -> None:
    prefs = LayoutPreferences.empty()
    assert prefs.sidebar_order == ()
    assert prefs.dashboard_blocks == ()
    assert prefs.updated_at is None


def test_layout_preferences_valido() -> None:
    bloques = (
        DashboardBlockPreference(id="/panel/resumen"),
        DashboardBlockPreference(id="/panel/grafico", visible=False),
    )
    prefs = LayoutPreferences(
        sidebar_order=("/panel", "/mascotas", "/citas"),
        dashboard_blocks=bloques,
    )
    assert prefs.sidebar_order == ("/panel", "/mascotas", "/citas")
    assert prefs.dashboard_blocks == bloques


def test_layout_preferences_limite_sidebar_excedido() -> None:
    items = tuple(f"/item/{i}" for i in range(51))
    with pytest.raises(LayoutLimitExceeded):
        LayoutPreferences(sidebar_order=items)


def test_layout_preferences_limite_dashboard_blocks_excedido() -> None:
    bloques = tuple(DashboardBlockPreference(id=f"/bloque/{i}") for i in range(51))
    with pytest.raises(LayoutLimitExceeded):
        LayoutPreferences(dashboard_blocks=bloques)


@pytest.mark.parametrize(
    "item_invalido",
    [
        "/Panel",
        "",
        "item con espacios",
        "/sidebar@1",
    ],
)
def test_layout_preferences_sidebar_item_invalido(item_invalido: str) -> None:
    with pytest.raises(InvalidLayoutIdentifier):
        LayoutPreferences(sidebar_order=(item_invalido,))


def test_layout_preferences_sidebar_duplicados() -> None:
    with pytest.raises(DuplicateLayoutIdentifier):
        LayoutPreferences(sidebar_order=("/panel", "/mascotas", "/panel"))


def test_layout_preferences_dashboard_blocks_duplicados() -> None:
    bloques = (
        DashboardBlockPreference(id="/panel/resumen", visible=True),
        DashboardBlockPreference(id="/panel/resumen", visible=False),
    )
    with pytest.raises(DuplicateLayoutIdentifier):
        LayoutPreferences(dashboard_blocks=bloques)


def test_user_layout_preference_entity() -> None:
    prefs = LayoutPreferences(
        sidebar_order=("/panel",),
        dashboard_blocks=(DashboardBlockPreference(id="/bloque/1"),),
    )
    user_layout = UserLayoutPreference(user_id=42, preferences=prefs)

    assert user_layout.user_id == 42
    assert user_layout.sidebar_order == ("/panel",)
    assert len(user_layout.dashboard_blocks) == 1
    assert user_layout.updated_at is None

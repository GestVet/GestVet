"""Casos de uso de preferencias de interfaz.

Permite consultar, guardar y restablecer la disposición personalizada del
sidebar y los bloques del panel principal para cualquier usuario autenticado.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from gestvet.modules.accounts.domain.entities import (
    DashboardBlockPreference,
    LayoutPreferences,
    UserLayoutPreference,
)
from gestvet.modules.accounts.domain.exceptions import InvalidLayoutPreferences
from gestvet.modules.accounts.ports.layout_repository import LayoutRepository


@dataclass(frozen=True, slots=True)
class SaveLayoutPreferencesCommand:
    user_id: int
    sidebar_order: Sequence[str]
    dashboard_blocks: Sequence[DashboardBlockPreference | dict[str, Any]]


class GetLayoutPreferences:
    """Obtiene las preferencias de interfaz del usuario o las vacías por defecto."""

    def __init__(self, layout_repository: LayoutRepository) -> None:
        self._layout_repository = layout_repository

    async def __call__(self, user_id: int) -> LayoutPreferences:
        record = await self._layout_repository.get_by_user_id(user_id)
        if record is None:
            return LayoutPreferences.empty()
        return record.preferences


class SaveLayoutPreferences:
    """Guarda o actualiza las preferencias de interfaz del usuario."""

    def __init__(self, layout_repository: LayoutRepository) -> None:
        self._layout_repository = layout_repository

    async def __call__(self, command: SaveLayoutPreferencesCommand) -> LayoutPreferences:
        blocks: list[DashboardBlockPreference] = []
        for item in command.dashboard_blocks:
            if isinstance(item, DashboardBlockPreference):
                blocks.append(item)
            elif isinstance(item, dict):
                blocks.append(
                    DashboardBlockPreference(
                        id=str(item.get("id", "")),
                        visible=bool(item.get("visible", True)),
                    )
                )
            else:
                raise InvalidLayoutPreferences("Estructura de bloque inválida.")

        preferences = LayoutPreferences(
            sidebar_order=tuple(command.sidebar_order),
            dashboard_blocks=tuple(blocks),
            updated_at=datetime.now(UTC),
        )

        user_layout = UserLayoutPreference(
            user_id=command.user_id,
            preferences=preferences,
        )
        saved = await self._layout_repository.save(user_layout)
        return saved.preferences


class ResetLayoutPreferences:
    """Restablece las preferencias de interfaz eliminando cualquier personalización."""

    def __init__(self, layout_repository: LayoutRepository) -> None:
        self._layout_repository = layout_repository

    async def __call__(self, user_id: int) -> None:
        await self._layout_repository.delete_by_user_id(user_id)

"""Puerto de lectura hacia `pets` y `medical_records`, para el panorama de mascotas."""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.insights.domain.entities import PetOverviewRecord

__all__ = ["PetOverviewDirectory", "PetOverviewRecord"]


class PetOverviewDirectory(Protocol):
    async def records(self, veterinarian_id: int | None) -> list[PetOverviewRecord]:
        """Todas las mascotas, o solo las que atendió ese veterinario si se indica."""
        ...

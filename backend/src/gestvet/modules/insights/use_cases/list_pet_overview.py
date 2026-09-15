"""Caso de uso: panorama de mascotas de la clínica."""

from __future__ import annotations

from datetime import date

from gestvet.modules.insights.domain.entities import PetOverview
from gestvet.modules.insights.domain.rules import build_pet_overview
from gestvet.modules.insights.ports.pet_overview_directory import PetOverviewDirectory


class ListPetOverview:
    def __init__(self, directory: PetOverviewDirectory) -> None:
        self._directory = directory

    async def __call__(self, veterinarian_id: int | None, today: date) -> list[PetOverview]:
        records = await self._directory.records(veterinarian_id)
        return build_pet_overview(records, today)

"""Caso de uso: qué servicios se consumen más."""

from __future__ import annotations

from datetime import datetime

from gestvet.modules.insights.domain.entities import ServiceConsumption
from gestvet.modules.insights.domain.rules import build_service_consumption
from gestvet.modules.insights.ports.service_consumption_directory import (
    ServiceConsumptionDirectory,
)


class ListServiceConsumption:
    def __init__(self, directory: ServiceConsumptionDirectory) -> None:
        self._directory = directory

    async def __call__(
        self,
        starts_after: datetime | None,
        ends_before: datetime | None,
        status: str | None,
    ) -> list[ServiceConsumption]:
        records = await self._directory.records(starts_after, ends_before, status)
        return build_service_consumption(records)

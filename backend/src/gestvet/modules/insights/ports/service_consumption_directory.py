"""Puerto de lectura hacia `appointments`, para servicios más consumidos."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from gestvet.modules.insights.domain.entities import ServiceConsumptionRecord

__all__ = ["ServiceConsumptionDirectory", "ServiceConsumptionRecord"]


class ServiceConsumptionDirectory(Protocol):
    async def records(
        self,
        starts_after: datetime | None,
        ends_before: datetime | None,
        status: str | None,
    ) -> list[ServiceConsumptionRecord]:
        """Cuántas citas tuvo cada tipo de servicio en el rango, filtrando por estado si se pide."""
        ...

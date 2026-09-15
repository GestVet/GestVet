"""Puerto del PDF de servicios más consumidos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from gestvet.modules.insights.domain.entities import ServiceConsumption


@dataclass(frozen=True, slots=True)
class ServiceConsumptionDocument:
    items: list[ServiceConsumption]
    starts_on: date | None
    ends_on: date | None
    status_label: str
    generated_at: date


class ServiceConsumptionRenderer(Protocol):
    def render(self, document: ServiceConsumptionDocument) -> bytes: ...

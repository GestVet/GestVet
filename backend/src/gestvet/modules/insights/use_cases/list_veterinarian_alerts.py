"""Caso de uso: veterinarios con reseñas bajas o reclamos recientes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gestvet.modules.insights.domain.entities import (
    VETERINARIAN_ALERT_WINDOW_DAYS,
    VeterinarianAlert,
)
from gestvet.modules.insights.domain.rules import build_veterinarian_alerts
from gestvet.modules.insights.ports.reputation_directory import ReputationDirectory


class ListVeterinarianAlerts:
    def __init__(self, reputation: ReputationDirectory) -> None:
        self._reputation = reputation

    async def __call__(self, now: datetime | None = None) -> list[VeterinarianAlert]:
        moment = now or datetime.now(UTC)
        since = moment - timedelta(days=VETERINARIAN_ALERT_WINDOW_DAYS)
        signals = await self._reputation.signals_since(since)
        return build_veterinarian_alerts(signals)

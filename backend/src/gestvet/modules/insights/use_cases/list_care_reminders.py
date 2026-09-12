"""Caso de uso: recordatorios de cuidado vencido."""

from __future__ import annotations

from datetime import UTC, datetime

from gestvet.modules.insights.domain.entities import CareReminder
from gestvet.modules.insights.domain.rules import build_care_reminders
from gestvet.modules.insights.ports.clinical_directory import ClinicalDirectory


class ListCareReminders:
    def __init__(self, clinical: ClinicalDirectory) -> None:
        self._clinical = clinical

    async def __call__(self, now: datetime | None = None) -> list[CareReminder]:
        records = await self._clinical.care_records()
        return build_care_reminders(records, now or datetime.now(UTC))

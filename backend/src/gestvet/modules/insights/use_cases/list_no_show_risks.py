"""Caso de uso: citas próximas con riesgo de inasistencia."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gestvet.modules.insights.domain.entities import (
    NO_SHOW_HISTORY_WINDOW_DAYS,
    NO_SHOW_UPCOMING_WINDOW_DAYS,
    NoShowRisk,
)
from gestvet.modules.insights.domain.rules import build_no_show_risks
from gestvet.modules.insights.ports.appointment_directory import AppointmentDirectory


class ListNoShowRisks:
    def __init__(self, appointments: AppointmentDirectory) -> None:
        self._appointments = appointments

    async def __call__(self, now: datetime | None = None) -> list[NoShowRisk]:
        moment = now or datetime.now(UTC)
        since = moment - timedelta(days=NO_SHOW_HISTORY_WINDOW_DAYS)
        until = moment + timedelta(days=NO_SHOW_UPCOMING_WINDOW_DAYS)
        records = await self._appointments.recent_and_upcoming(since, until)
        return build_no_show_risks(records, moment)

"""Puerto de lectura hacia `appointments`, `pets` y `accounts`."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from gestvet.modules.insights.domain.entities import AppointmentRecord

__all__ = ["AppointmentDirectory", "AppointmentRecord"]


class AppointmentDirectory(Protocol):
    async def recent_and_upcoming(
        self, since: datetime, until: datetime
    ) -> list[AppointmentRecord]: ...

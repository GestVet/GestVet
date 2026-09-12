"""Puerto de lectura hacia `reviews`, `complaints` y `accounts`."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from gestvet.modules.insights.domain.entities import VeterinarianSignal

__all__ = ["ReputationDirectory", "VeterinarianSignal"]


class ReputationDirectory(Protocol):
    async def signals_since(self, since: datetime) -> list[VeterinarianSignal]: ...

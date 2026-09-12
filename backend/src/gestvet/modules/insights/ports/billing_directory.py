"""Puerto de lectura hacia `billing` y `appointments`."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from gestvet.modules.insights.domain.entities import PaymentRecord

__all__ = ["BillingDirectory", "PaymentRecord"]


class BillingDirectory(Protocol):
    async def payments_since(self, since: datetime) -> list[PaymentRecord]: ...

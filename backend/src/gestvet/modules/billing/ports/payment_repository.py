"""Puerto de persistencia de los pagos.

Define qué necesita el negocio, nunca cómo se guarda.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page
from gestvet.modules.billing.domain.entities import Payment, PaymentMethod


@dataclass(frozen=True, slots=True)
class PaymentQuery:
    appointment_id: int | None = None
    client_id: int | None = None
    method: PaymentMethod | None = None
    include_voided: bool = True
    starts_after: datetime | None = None
    ends_before: datetime | None = None
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


@dataclass(frozen=True, slots=True)
class MethodTotal:
    """Una fila del reporte: cuánto entró por un medio de cobro."""

    method: PaymentMethod
    total: Decimal
    count: int


class PaymentRepository(Protocol):
    async def add(self, payment: Payment) -> Payment: ...

    async def get(self, payment_id: int) -> Payment | None: ...

    async def save(self, payment: Payment) -> Payment: ...

    async def search(self, query: PaymentQuery) -> Page[Payment]: ...

    async def totals_by_method(self, query: PaymentQuery) -> list[MethodTotal]: ...

"""Caso de uso: cuánto entró y por qué medio, en un rango de fechas.

Es cosa de la administración: ver el total cobrado es más sensible que ver un
cobro puntual, que ya puede consultar cualquiera del personal.
"""

from __future__ import annotations

from datetime import datetime

from gestvet.modules.billing.ports.payment_repository import (
    MethodTotal,
    PaymentQuery,
    PaymentRepository,
)


class BuildPaymentReport:
    def __init__(self, payments: PaymentRepository) -> None:
        self._payments = payments

    async def __call__(
        self, *, starts_after: datetime | None, ends_before: datetime | None
    ) -> list[MethodTotal]:
        return await self._payments.totals_by_method(
            PaymentQuery(
                include_voided=False,
                starts_after=starts_after,
                ends_before=ends_before,
            )
        )

"""Caso de uso: pagos cuyo monto se aleja del típico de su tipo de cita."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gestvet.modules.insights.domain.entities import PAYMENT_ANOMALY_WINDOW_DAYS, PaymentAnomaly
from gestvet.modules.insights.domain.rules import build_payment_anomalies
from gestvet.modules.insights.ports.billing_directory import BillingDirectory


class ListPaymentAnomalies:
    def __init__(self, billing: BillingDirectory) -> None:
        self._billing = billing

    async def __call__(self, now: datetime | None = None) -> list[PaymentAnomaly]:
        moment = now or datetime.now(UTC)
        since = moment - timedelta(days=PAYMENT_ANOMALY_WINDOW_DAYS)
        records = await self._billing.payments_since(since)
        return build_payment_anomalies(records)

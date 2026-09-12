"""Caso de uso: anular un pago registrado por error."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.billing.domain.entities import Payment
from gestvet.modules.billing.domain.exceptions import PaymentNotFound
from gestvet.modules.billing.ports.payment_repository import PaymentRepository


@dataclass(frozen=True, slots=True)
class VoidPaymentCommand:
    payment_id: int
    actor_id: int
    reason: str


class VoidPayment:
    def __init__(self, payments: PaymentRepository, activity: ActivityRecorder) -> None:
        self._payments = payments
        self._activity = activity

    async def __call__(self, command: VoidPaymentCommand) -> Payment:
        payment = await self._payments.get(command.payment_id)
        if payment is None:
            raise PaymentNotFound(command.payment_id)

        payment.void(command.reason, datetime.now(UTC))
        guardado = await self._payments.save(payment)
        await self._activity.record(
            command.actor_id, ActivityKind.PAYMENT_VOIDED, guardado.void_reason
        )
        return guardado

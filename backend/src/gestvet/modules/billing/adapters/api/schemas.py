"""Contrato HTTP del módulo de pagos."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from gestvet.modules.billing.domain.entities import (
    MAX_NOTES_LENGTH,
    MAX_REFERENCE_LENGTH,
    MAX_VOID_REASON_LENGTH,
    Payment,
    PaymentMethod,
)
from gestvet.modules.billing.ports.payment_repository import MethodTotal


class RegisterPaymentRequest(BaseModel):
    appointment_id: int = Field(ge=1)
    amount: Decimal = Field(gt=0)
    method: PaymentMethod
    reference: str = Field(default="", max_length=MAX_REFERENCE_LENGTH)
    notes: str = Field(default="", max_length=MAX_NOTES_LENGTH)


class VoidPaymentRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=MAX_VOID_REASON_LENGTH)


class PaymentResponse(BaseModel):
    id: int
    appointment_id: int
    client_id: int
    registered_by: int
    amount: Decimal
    method: PaymentMethod
    method_label: str
    reference: str
    notes: str
    is_voided: bool
    voided_at: datetime | None
    void_reason: str
    paid_at: datetime
    created_at: datetime

    @classmethod
    def from_entity(cls, payment: Payment) -> PaymentResponse:
        return cls(
            id=payment.id or 0,
            appointment_id=payment.appointment_id,
            client_id=payment.client_id,
            registered_by=payment.registered_by,
            amount=payment.amount,
            method=payment.method,
            method_label=payment.method.label,
            reference=payment.reference,
            notes=payment.notes,
            is_voided=payment.is_voided,
            voided_at=payment.voided_at,
            void_reason=payment.void_reason,
            paid_at=payment.paid_at,
            created_at=payment.created_at,
        )


class PaymentPageResponse(BaseModel):
    items: list[PaymentResponse]
    total: int


class MethodTotalResponse(BaseModel):
    method: PaymentMethod
    method_label: str
    total: Decimal
    count: int

    @classmethod
    def from_entity(cls, item: MethodTotal) -> MethodTotalResponse:
        return cls(
            method=item.method,
            method_label=item.method.label,
            total=item.total,
            count=item.count,
        )


class PaymentReportResponse(BaseModel):
    items: list[MethodTotalResponse]
    grand_total: Decimal

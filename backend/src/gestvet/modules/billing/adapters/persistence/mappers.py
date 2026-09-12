"""Traducción entre la fila de la tabla y la entidad de dominio.

Este archivo es la razón por la que el dominio puede ignorar SQLAlchemy.
"""

from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.billing.adapters.persistence.models import PaymentRow
from gestvet.modules.billing.domain.entities import Payment, PaymentMethod


def row_to_entity(row: PaymentRow) -> Payment:
    return Payment(
        id=row.id,
        appointment_id=row.appointment_id,
        client_id=row.client_id,
        registered_by=row.registered_by,
        amount=row.amount,
        method=PaymentMethod(row.method),
        reference=row.reference,
        notes=row.notes,
        voided_at=as_utc(row.voided_at) if row.voided_at else None,
        void_reason=row.void_reason,
        paid_at=as_utc(row.paid_at),
        created_at=as_utc(row.created_at),
    )


def entity_to_row(payment: Payment) -> PaymentRow:
    return PaymentRow(
        appointment_id=payment.appointment_id,
        client_id=payment.client_id,
        registered_by=payment.registered_by,
        amount=payment.amount,
        method=payment.method.value,
        reference=payment.reference,
        notes=payment.notes,
        voided_at=payment.voided_at,
        void_reason=payment.void_reason,
        paid_at=payment.paid_at,
        created_at=payment.created_at,
    )

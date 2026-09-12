"""Traducción entre la fila de la tabla y la entidad de dominio.

Este archivo es la razón por la que el dominio puede ignorar SQLAlchemy.
"""

from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.billing.adapters.persistence.models import PaymentRow, QrChargeRow
from gestvet.modules.billing.domain.entities import Payment, PaymentMethod
from gestvet.modules.billing.domain.qr_charge import QrCharge, QrChargeStatus


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


def qr_charge_row_to_entity(row: QrChargeRow) -> QrCharge:
    return QrCharge(
        id=row.id,
        appointment_id=row.appointment_id,
        client_id=row.client_id,
        amount=row.amount,
        status=QrChargeStatus(row.status),
        gateway_charge_id=row.gateway_charge_id,
        qr_image_data_url=row.qr_image_data_url,
        payment_id=row.payment_id,
        expires_at=as_utc(row.expires_at),
        confirmed_at=as_utc(row.confirmed_at) if row.confirmed_at else None,
        created_at=as_utc(row.created_at),
    )


def qr_charge_entity_to_row(charge: QrCharge) -> QrChargeRow:
    return QrChargeRow(
        appointment_id=charge.appointment_id,
        client_id=charge.client_id,
        amount=charge.amount,
        status=charge.status.value,
        gateway_charge_id=charge.gateway_charge_id,
        qr_image_data_url=charge.qr_image_data_url,
        payment_id=charge.payment_id,
        expires_at=charge.expires_at,
        confirmed_at=charge.confirmed_at,
        created_at=charge.created_at,
    )

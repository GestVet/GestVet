"""Entidad de dominio: un cobro por QR en curso.

Vive aparte de `Payment` porque su ciclo de vida es distinto: un pago
registrado a mano nace completo, este nace pendiente y solo se confirma si
alguien paga. Confirmado, genera un `Payment` de verdad; el cobro por QR en
sí mismo nunca es "el pago", es el trámite para llegar a uno.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from gestvet.modules.billing.domain.exceptions import InvalidPayment, QrChargeNotPending

# Un QR de cobro no queda abierto para siempre: quince minutos alcanza para
# escanearlo y pagar, y evita que uno viejo aparezca como cobrable meses
# después.
QR_CHARGE_TTL_MINUTES = 15


class QrChargeStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]


_STATUS_LABELS: dict[QrChargeStatus, str] = {
    QrChargeStatus.PENDING: "Pendiente",
    QrChargeStatus.PAID: "Pagado",
    QrChargeStatus.EXPIRED: "Vencido",
    QrChargeStatus.CANCELLED: "Cancelado",
}


def _default_expiration() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=QR_CHARGE_TTL_MINUTES)


@dataclass(slots=True)
class QrCharge:
    appointment_id: int
    client_id: int
    amount: Decimal
    gateway_charge_id: str
    qr_image_data_url: str
    status: QrChargeStatus = QrChargeStatus.PENDING
    payment_id: int | None = None
    id: int | None = None
    expires_at: datetime = field(default_factory=_default_expiration)
    confirmed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise InvalidPayment("El monto debe ser positivo.")

    def effective_status(self, now: datetime | None = None) -> QrChargeStatus:
        """El estado que corresponde en este instante.

        Un cobro pendiente vencido no deja de estarlo porque nadie volvió a
        mirarlo: se calcula al leer, en vez de necesitar un trabajo en
        segundo plano que lo marque.
        """
        reference = now or datetime.now(UTC)
        if self.status is QrChargeStatus.PENDING and reference >= self.expires_at:
            return QrChargeStatus.EXPIRED
        return self.status

    def confirm(self, payment_id: int, now: datetime | None = None) -> None:
        reference = now or datetime.now(UTC)
        if self.effective_status(reference) is not QrChargeStatus.PENDING:
            raise QrChargeNotPending(self.id or 0)
        self.status = QrChargeStatus.PAID
        self.payment_id = payment_id
        self.confirmed_at = reference

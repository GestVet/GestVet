"""Entidades de dominio de los pagos.

Python puro. La cita y las cuentas se referencian por identificador: cada una
vive en otro módulo y este no puede importarlas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from gestvet.modules.billing.domain.exceptions import InvalidPayment, PaymentAlreadyVoided

MAX_REFERENCE_LENGTH = 120
MAX_NOTES_LENGTH = 300
MAX_VOID_REASON_LENGTH = 300


class PaymentMethod(StrEnum):
    CASH = "cash"
    YAPE = "yape"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"

    @property
    def label(self) -> str:
        return _METHOD_LABELS[self]


_METHOD_LABELS: dict[PaymentMethod, str] = {
    PaymentMethod.CASH: "Efectivo",
    PaymentMethod.YAPE: "Yape",
    PaymentMethod.BANK_TRANSFER: "Transferencia bancaria",
    PaymentMethod.OTHER: "Otro",
}


@dataclass(slots=True)
class Payment:
    """Un cobro registrado a mano, nunca una pasarela de por medio.

    Una vez registrado no se edita ni se borra: un error se corrige
    anulándolo, con motivo, y quien necesite el monto correcto registra un
    pago nuevo. Es la misma idea que ya usa la bitácora: el historial no se
    reescribe.
    """

    appointment_id: int
    client_id: int
    amount: Decimal
    method: PaymentMethod
    registered_by: int
    reference: str = ""
    notes: str = ""
    voided_at: datetime | None = None
    void_reason: str = ""
    id: int | None = None
    paid_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise InvalidPayment("El monto debe ser positivo.")
        self.reference = _trim(self.reference, "referencia", MAX_REFERENCE_LENGTH)
        self.notes = _trim(self.notes, "notas", MAX_NOTES_LENGTH)

    @property
    def is_voided(self) -> bool:
        return self.voided_at is not None

    def void(self, reason: str, now: datetime) -> None:
        if self.is_voided:
            raise PaymentAlreadyVoided(self.id or 0)
        cleaned = reason.strip()
        if not cleaned:
            raise InvalidPayment("Anular un pago exige indicar el motivo.")
        if len(cleaned) > MAX_VOID_REASON_LENGTH:
            raise InvalidPayment(
                f"El motivo admite {MAX_VOID_REASON_LENGTH} caracteres como máximo."
            )
        self.voided_at = now
        self.void_reason = cleaned


def _trim(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if len(value) > max_length:
        raise InvalidPayment(f"El campo {field_name!r} admite {max_length} caracteres como máximo.")
    return value

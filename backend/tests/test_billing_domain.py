"""Pruebas del dominio de los pagos. Python puro, sin base ni servidor."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from gestvet.modules.billing.domain.entities import Payment, PaymentMethod
from gestvet.modules.billing.domain.exceptions import InvalidPayment, PaymentAlreadyVoided

AHORA = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)


def _pago(**overrides: object) -> Payment:
    valores: dict[str, object] = {
        "appointment_id": 1,
        "client_id": 2,
        "amount": Decimal("60.00"),
        "method": PaymentMethod.CASH,
        "registered_by": 3,
    }
    valores.update(overrides)
    return Payment(**valores)  # type: ignore[arg-type]


def test_el_monto_debe_ser_positivo() -> None:
    with pytest.raises(InvalidPayment):
        _pago(amount=Decimal("0"))
    with pytest.raises(InvalidPayment):
        _pago(amount=Decimal("-10"))


def test_cada_metodo_tiene_etiqueta() -> None:
    assert PaymentMethod.YAPE.label == "Yape"
    assert PaymentMethod.BANK_TRANSFER.label == "Transferencia bancaria"
    assert PaymentMethod.QR.label == "QR"


def test_un_pago_recien_creado_no_esta_anulado() -> None:
    pago = _pago()

    assert pago.is_voided is False


def test_anular_exige_motivo() -> None:
    pago = _pago()

    with pytest.raises(InvalidPayment):
        pago.void("   ", AHORA)


def test_anular_deja_el_pago_marcado() -> None:
    pago = _pago()

    pago.void("Se cargó el monto equivocado", AHORA)

    assert pago.is_voided is True
    assert pago.void_reason == "Se cargó el monto equivocado"
    assert pago.voided_at == AHORA


def test_un_pago_no_se_anula_dos_veces() -> None:
    pago = _pago()
    pago.void("Primer motivo", AHORA)

    with pytest.raises(PaymentAlreadyVoided):
        pago.void("Segundo motivo", AHORA)

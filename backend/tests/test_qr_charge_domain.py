"""Pruebas del dominio del cobro por QR. Python puro, sin base ni servidor."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from gestvet.modules.billing.domain.exceptions import InvalidPayment, QrChargeNotPending
from gestvet.modules.billing.domain.qr_charge import QrCharge, QrChargeStatus

AHORA = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)


def _cobro(**overrides: object) -> QrCharge:
    valores: dict[str, object] = {
        "appointment_id": 1,
        "client_id": 2,
        "amount": Decimal("60.00"),
        "gateway_charge_id": "sandbox-abc123",
        "qr_image_data_url": "data:image/png;base64,AAA",
        "expires_at": AHORA + timedelta(minutes=15),
    }
    valores.update(overrides)
    return QrCharge(**valores)  # type: ignore[arg-type]


def test_el_monto_debe_ser_positivo() -> None:
    with pytest.raises(InvalidPayment):
        _cobro(amount=Decimal("0"))


def test_nace_pendiente() -> None:
    cobro = _cobro()

    assert cobro.effective_status(AHORA) is QrChargeStatus.PENDING


def test_un_pendiente_vencido_se_ve_como_vencido() -> None:
    cobro = _cobro()
    despues_de_vencer = cobro.expires_at + timedelta(seconds=1)

    assert cobro.effective_status(despues_de_vencer) is QrChargeStatus.EXPIRED
    # El estado guardado no cambia solo por leerlo.
    assert cobro.status is QrChargeStatus.PENDING


def test_confirmar_deja_el_cobro_pagado() -> None:
    cobro = _cobro()

    cobro.confirm(payment_id=99, now=AHORA)

    assert cobro.status is QrChargeStatus.PAID
    assert cobro.payment_id == 99
    assert cobro.confirmed_at == AHORA


def test_no_se_confirma_dos_veces() -> None:
    cobro = _cobro()
    cobro.confirm(payment_id=99, now=AHORA)

    with pytest.raises(QrChargeNotPending):
        cobro.confirm(payment_id=100, now=AHORA)


def test_no_se_confirma_un_cobro_vencido() -> None:
    cobro = _cobro()
    despues_de_vencer = cobro.expires_at + timedelta(seconds=1)

    with pytest.raises(QrChargeNotPending):
        cobro.confirm(payment_id=99, now=despues_de_vencer)


def test_cada_estado_tiene_etiqueta() -> None:
    assert QrChargeStatus.PENDING.label == "Pendiente"
    assert QrChargeStatus.PAID.label == "Pagado"
    assert QrChargeStatus.EXPIRED.label == "Vencido"

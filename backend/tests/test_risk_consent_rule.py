"""Cuándo una aceptación de riesgo habilita abrir una emergencia."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from gestvet.modules.appointments.domain.exceptions import RiskConsentRejected
from gestvet.modules.appointments.domain.risk_consent import (
    RiskConsentFacts,
    ensure_risk_consent_usable,
)

AHORA = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


BASE = RiskConsentFacts(
    kind="emergency_risk",
    status="accepted",
    client_id=4,
    pet_id=3,
    decided_at=AHORA - timedelta(minutes=5),
    used_by_appointment=False,
)


def test_una_firma_reciente_del_mismo_dueno_y_mascota_habilita() -> None:
    ensure_risk_consent_usable(BASE, client_id=4, pet_id=3, now=AHORA)


@pytest.mark.parametrize(
    ("hechos", "fragmento"),
    [
        (None, "No encontramos"),
        (replace(BASE, client_id=9), "No encontramos"),
        (replace(BASE, kind="anesthesia"), "No encontramos"),
        (replace(BASE, status="declined"), "No encontramos"),
        (replace(BASE, pet_id=8), "otra mascota"),
        (replace(BASE, used_by_appointment=True), "ya se usó"),
        (replace(BASE, decided_at=AHORA - timedelta(minutes=31)), "30 minutos"),
    ],
)
def test_una_firma_que_no_sirve_dice_por_que(
    hechos: RiskConsentFacts | None, fragmento: str
) -> None:
    with pytest.raises(RiskConsentRejected, match=fragmento):
        ensure_risk_consent_usable(hechos, client_id=4, pet_id=3, now=AHORA)

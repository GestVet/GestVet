"""Reglas del dominio de consentimientos, sin base ni HTTP."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from gestvet.modules.consents.domain.entities import (
    Consent,
    ConsentChannel,
    ConsentKind,
    ConsentStatus,
    ConsentTemplate,
    fingerprint,
    normalize_signer_name,
)
from gestvet.modules.consents.domain.exceptions import InvalidConsent, InvalidSignerName

PLANTILLA = ConsentTemplate(
    id=7,
    kind=ConsentKind.EMERGENCY_RISK,
    version=1,
    title="Riesgo",
    body="Mi mascota puede morir.",
)


def test_el_nombre_se_recorta_y_colapsa_los_espacios() -> None:
    assert normalize_signer_name("  Ana    María   Quispe ") == "Ana María Quispe"


@pytest.mark.parametrize("nombre", ["", "   ", "Ana", "  Quispe  "])
def test_una_sola_palabra_no_alcanza_como_firma(nombre: str) -> None:
    with pytest.raises(InvalidSignerName):
        normalize_signer_name(nombre)


def test_el_nombre_tiene_un_tope() -> None:
    with pytest.raises(InvalidSignerName):
        normalize_signer_name("Ana " + "Q" * 120)
    assert normalize_signer_name("Ana " + "Q" * 116) == "Ana " + "Q" * 116


def test_aceptar_copia_el_texto_y_su_huella() -> None:
    firmado = Consent.accept(
        PLANTILLA,
        pet_id=3,
        client_id=4,
        channel=ConsentChannel.ONLINE,
        signer_name="Ana  Quispe",
        signer_user_id=4,
    )

    assert firmado.status is ConsentStatus.ACCEPTED
    assert firmado.template_id == 7
    assert firmado.kind is ConsentKind.EMERGENCY_RISK
    assert firmado.text_snapshot == "Riesgo\n\nMi mascota puede morir."
    assert firmado.text_sha256 == fingerprint(firmado.text_snapshot)
    assert len(firmado.text_sha256) == 64
    assert firmado.signer_name == "Ana Quispe"


def test_una_huella_que_no_corresponde_al_texto_se_rechaza() -> None:
    with pytest.raises(InvalidConsent):
        Consent(
            template_id=7,
            kind=ConsentKind.EMERGENCY_RISK,
            pet_id=3,
            client_id=4,
            status=ConsentStatus.ACCEPTED,
            channel=ConsentChannel.ONLINE,
            text_snapshot="Texto leído",
            text_sha256=fingerprint("Otro texto"),
            signer_name="Ana Quispe",
            decided_at=datetime.now(UTC),
        )


def test_uno_presencial_necesita_testigo() -> None:
    with pytest.raises(InvalidConsent):
        Consent.accept(
            PLANTILLA,
            pet_id=3,
            client_id=4,
            channel=ConsentChannel.IN_PERSON,
            signer_name="Ana Quispe",
        )


def test_solo_lo_ve_su_dueno_o_el_personal() -> None:
    firmado = Consent.accept(
        PLANTILLA, pet_id=3, client_id=4, channel=ConsentChannel.ONLINE, signer_name="Ana Quispe"
    )

    assert firmado.visible_to(4, is_staff=False)
    assert not firmado.visible_to(5, is_staff=False)
    assert firmado.visible_to(5, is_staff=True)

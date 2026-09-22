"""Reglas de dominio de los consentimientos que pide el veterinario."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from gestvet.modules.consents.domain.appointment_facts import AppointmentFacts, ensure_visible
from gestvet.modules.consents.domain.details import DETAILS_HEADING, ConsentDetails
from gestvet.modules.consents.domain.entities import (
    PENDING_VALIDITY,
    Consent,
    ConsentChannel,
    ConsentKind,
    ConsentStatus,
    ConsentTemplate,
    fingerprint,
)
from gestvet.modules.consents.domain.exceptions import (
    AppointmentCancelled,
    AppointmentNotFound,
    ConsentExpired,
    ConsentNotPending,
    InvalidConsent,
    InvalidConsentDetails,
    InvalidSignerName,
    InvalidWaiver,
    WaiverOnlyForEmergencies,
)

AHORA = datetime(2026, 9, 21, 15, 0, tzinfo=UTC)
PLANTILLA = ConsentTemplate(
    id=3, kind=ConsentKind.PROCEDURE, version=1, title="Cirugía", body="Autorizo la cirugía."
)


def _pedido(details: ConsentDetails | None = None) -> Consent:
    return Consent.request(
        PLANTILLA,
        appointment_id=10,
        pet_id=3,
        client_id=4,
        requested_by=9,
        details=details or ConsentDetails.build(procedure="Castración"),
        now=AHORA,
    )


def _cita(*, status: str = "confirmed", is_emergency: bool = False) -> AppointmentFacts:
    return AppointmentFacts(
        id=10, client_id=4, pet_id=3, veterinarian_id=9, status=status, is_emergency=is_emergency
    )


@pytest.mark.parametrize(
    "kind", [ConsentKind.PROCEDURE, ConsentKind.ANESTHESIA, ConsentKind.EUTHANASIA]
)
def test_algunos_tipos_exigen_el_procedimiento(kind: ConsentKind) -> None:
    assert kind.requires_procedure
    with pytest.raises(InvalidConsentDetails):
        ConsentDetails.build(procedure="   ", procedure_required=kind.requires_procedure)


@pytest.mark.parametrize("kind", [ConsentKind.HIGH_RISK, ConsentKind.HOSPITALIZATION])
def test_otros_tipos_no_exigen_el_procedimiento(kind: ConsentKind) -> None:
    assert not kind.requires_procedure
    assert ConsentDetails.build(procedure_required=kind.requires_procedure).is_empty


def test_el_riesgo_de_emergencia_no_se_pide_desde_una_cita() -> None:
    assert not ConsentKind.EMERGENCY_RISK.requestable
    assert all(kind.requestable for kind in ConsentKind if kind is not ConsentKind.EMERGENCY_RISK)


def test_el_detalle_valida_topes_y_costo() -> None:
    with pytest.raises(InvalidConsentDetails):
        ConsentDetails.build(procedure="x" * 201)
    with pytest.raises(InvalidConsentDetails):
        ConsentDetails.build(estimated_cost=Decimal(0))
    with pytest.raises(InvalidConsentDetails):
        ConsentDetails.build(estimated_cost=Decimal("2000000"))
    assert ConsentDetails.build(estimated_cost=Decimal("150.456")).estimated_cost == Decimal(
        "150.46"
    )


def test_el_pedido_copia_el_texto_con_el_detalle_debajo() -> None:
    pedido = _pedido(
        ConsentDetails.build(
            procedure="Castración",
            prognosis="Bueno",
            estimated_cost=Decimal("1250"),
            notes="Ayuno de 8 horas",
        )
    )

    assert pedido.status is ConsentStatus.PENDING
    assert pedido.channel is None and pedido.signer_name is None and pedido.decided_at is None
    assert pedido.text_snapshot.startswith("Cirugía\n\nAutorizo la cirugía.\n\n" + DETAILS_HEADING)
    assert "- Procedimiento: Castración" in pedido.text_snapshot
    assert "- Pronóstico: Bueno" in pedido.text_snapshot
    assert "S/ 1,250.00" in pedido.text_snapshot
    assert "- Observaciones: Ayuno de 8 horas" in pedido.text_snapshot
    assert pedido.text_sha256 == fingerprint(pedido.text_snapshot)
    assert pedido.details == {
        "procedure": "Castración",
        "prognosis": "Bueno",
        "estimated_cost": "1250.00",
        "notes": "Ayuno de 8 horas",
    }


def test_sin_detalle_el_texto_es_el_de_la_plantilla() -> None:
    plantilla = ConsentTemplate(
        id=5, kind=ConsentKind.HOSPITALIZATION, version=1, title="Internación", body="Autorizo."
    )
    pedido = Consent.request(
        plantilla,
        appointment_id=1,
        pet_id=1,
        client_id=1,
        requested_by=2,
        details=ConsentDetails.build(),
    )
    assert pedido.text_snapshot == plantilla.render()
    assert pedido.details is None


def test_un_pedido_vence_a_las_24_horas() -> None:
    pedido = _pedido()

    assert pedido.expires_at == AHORA + PENDING_VALIDITY
    assert pedido.effective_status(AHORA + timedelta(hours=23)) is ConsentStatus.PENDING
    assert pedido.effective_status(AHORA + PENDING_VALIDITY) is ConsentStatus.EXPIRED
    with pytest.raises(ConsentExpired):
        pedido.accept_request(
            signer_name="Ana Quispe",
            channel=ConsentChannel.ONLINE,
            now=AHORA + timedelta(hours=25),
        )


def test_aceptar_un_pedido_guarda_la_firma_sin_tocar_el_texto() -> None:
    pedido = _pedido()
    texto = pedido.text_snapshot

    pedido.accept_request(
        signer_name=" Ana  Quispe ",
        channel=ConsentChannel.ONLINE,
        signer_user_id=4,
        now=AHORA + timedelta(hours=1),
    )

    assert pedido.status is ConsentStatus.ACCEPTED
    assert pedido.signer_name == "Ana Quispe"
    assert pedido.decided_at == AHORA + timedelta(hours=1)
    assert pedido.text_snapshot == texto
    assert pedido.expires_at is None


def test_aceptar_pide_nombre_completo_y_en_persona_testigo() -> None:
    with pytest.raises(InvalidSignerName):
        _pedido().accept_request(signer_name="Ana", channel=ConsentChannel.ONLINE, now=AHORA)
    with pytest.raises(InvalidConsent):
        _pedido().accept_request(
            signer_name="Ana Quispe", channel=ConsentChannel.IN_PERSON, now=AHORA
        )


def test_no_se_responde_dos_veces() -> None:
    pedido = _pedido()
    pedido.decline(reason="Prefiero pensarlo", signer_user_id=4, now=AHORA)

    assert pedido.status is ConsentStatus.DECLINED
    assert pedido.decision_reason == "Prefiero pensarlo"
    with pytest.raises(ConsentNotPending):
        pedido.accept_request(signer_name="Ana Quispe", channel=ConsentChannel.ONLINE, now=AHORA)


def test_el_motivo_del_rechazo_es_opcional_y_acotado() -> None:
    pedido = _pedido()
    pedido.decline(reason="   ", signer_user_id=4, now=AHORA)
    assert pedido.decision_reason is None
    with pytest.raises(InvalidConsent):
        _pedido().decline(reason="x" * 501, signer_user_id=4, now=AHORA)


@pytest.mark.parametrize("justificacion", ["", "Urgente", "x" * 19, "x" * 1001])
def test_la_urgencia_vital_exige_una_justificacion_real(justificacion: str) -> None:
    with pytest.raises(InvalidWaiver):
        Consent.waive(
            PLANTILLA,
            appointment_id=10,
            pet_id=3,
            client_id=4,
            recorded_by=9,
            justification=justificacion,
        )


def test_la_urgencia_vital_queda_registrada() -> None:
    eximido = Consent.waive(
        PLANTILLA,
        appointment_id=10,
        pet_id=3,
        client_id=4,
        recorded_by=9,
        justification="  Paro respiratorio, el dueño no contesta el teléfono.  ",
        now=AHORA,
    )

    assert eximido.status is ConsentStatus.WAIVED_EMERGENCY
    assert eximido.decision_reason == "Paro respiratorio, el dueño no contesta el teléfono."
    assert eximido.requested_by == 9
    assert eximido.channel is None
    assert eximido.effective_status(AHORA + timedelta(days=3)) is ConsentStatus.WAIVED_EMERGENCY


def test_la_cita_decide_si_se_puede_pedir_o_eximir() -> None:
    with pytest.raises(AppointmentCancelled):
        _cita(status="cancelled").ensure_open_for_consents()
    with pytest.raises(WaiverOnlyForEmergencies):
        _cita().ensure_emergency()
    _cita(is_emergency=True).ensure_emergency()


def test_la_cita_de_otro_veterinario_no_existe() -> None:
    with pytest.raises(AppointmentNotFound):
        ensure_visible(_cita(), 10, user_id=77, sees_all=False)
    with pytest.raises(AppointmentNotFound):
        ensure_visible(None, 10, user_id=9, sees_all=True)
    assert ensure_visible(_cita(), 10, user_id=77, sees_all=True).id == 10

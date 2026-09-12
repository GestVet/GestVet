"""Pruebas de las reglas del panel de indicadores. Python puro, sin base."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from gestvet.modules.insights.domain.entities import AppointmentRecord, PaymentRecord, PetCareRecord
from gestvet.modules.insights.domain.rules import (
    build_care_reminders,
    build_no_show_risks,
    build_payment_anomalies,
    build_veterinarian_alerts,
)
from gestvet.modules.insights.ports.reputation_directory import VeterinarianSignal

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)


def _pet(**overrides: object) -> PetCareRecord:
    valores: dict[str, object] = {
        "pet_id": 1,
        "pet_name": "Rocco",
        "owner_id": 2,
        "owner_name": "Ana Quispe",
        "registered_at": NOW - timedelta(days=900),
        "last_vaccine_at": None,
        "last_checkup_at": None,
    }
    valores.update(overrides)
    return PetCareRecord(**valores)  # type: ignore[arg-type]


def test_recuerda_la_vacuna_vencida() -> None:
    mascota = _pet(
        last_vaccine_at=NOW - timedelta(days=400), last_checkup_at=NOW - timedelta(days=1)
    )

    recordatorios = build_care_reminders([mascota], NOW)

    assert any(r.reason == "vacuna" for r in recordatorios)
    assert not any(r.reason == "control" for r in recordatorios)


def test_no_recuerda_lo_que_esta_al_dia() -> None:
    mascota = _pet(
        last_vaccine_at=NOW - timedelta(days=10), last_checkup_at=NOW - timedelta(days=10)
    )

    assert build_care_reminders([mascota], NOW) == []


def test_sin_historia_clinica_usa_la_fecha_de_registro() -> None:
    mascota = _pet(registered_at=NOW - timedelta(days=400))

    recordatorios = build_care_reminders([mascota], NOW)

    razones = {r.reason for r in recordatorios}
    assert razones == {"vacuna", "control"}


def _appointment(**overrides: object) -> AppointmentRecord:
    valores: dict[str, object] = {
        "appointment_id": 1,
        "client_id": 1,
        "client_name": "Ana Quispe",
        "pet_name": "Rocco",
        "scheduled_at": NOW + timedelta(days=1),
        "ends_at": NOW + timedelta(days=1, minutes=30),
        "status": "confirmed",
    }
    valores.update(overrides)
    return AppointmentRecord(**valores)  # type: ignore[arg-type]


def test_marca_riesgo_con_dos_inasistencias_previas() -> None:
    pasada_1 = _appointment(
        appointment_id=1, scheduled_at=NOW - timedelta(days=10), ends_at=NOW - timedelta(days=10)
    )
    pasada_2 = _appointment(
        appointment_id=2, scheduled_at=NOW - timedelta(days=5), ends_at=NOW - timedelta(days=5)
    )
    proxima = _appointment(appointment_id=3)

    riesgos = build_no_show_risks([pasada_1, pasada_2, proxima], NOW)

    assert len(riesgos) == 1
    assert riesgos[0].appointment_id == 3
    assert riesgos[0].past_incidents == 2


def test_una_sola_inasistencia_previa_no_alcanza() -> None:
    pasada = _appointment(
        appointment_id=1, scheduled_at=NOW - timedelta(days=10), ends_at=NOW - timedelta(days=10)
    )
    proxima = _appointment(appointment_id=2)

    assert build_no_show_risks([pasada, proxima], NOW) == []


def test_una_cita_completada_no_cuenta_como_inasistencia() -> None:
    completada = _appointment(
        appointment_id=1,
        scheduled_at=NOW - timedelta(days=10),
        ends_at=NOW - timedelta(days=10),
        status="completed",
    )
    otra = _appointment(
        appointment_id=2, scheduled_at=NOW - timedelta(days=5), ends_at=NOW - timedelta(days=5)
    )
    proxima = _appointment(appointment_id=3)

    assert build_no_show_risks([completada, otra, proxima], NOW) == []


def _payment(**overrides: object) -> PaymentRecord:
    valores: dict[str, object] = {
        "payment_id": 1,
        "appointment_id": 1,
        "client_id": 1,
        "appointment_type_id": 1,
        "appointment_type_label": "Consulta general",
        "is_emergency_type": False,
        "amount": Decimal("50"),
        "paid_at": NOW,
    }
    valores.update(overrides)
    return PaymentRecord(**valores)  # type: ignore[arg-type]


def test_detecta_un_monto_fuera_de_lo_tipico() -> None:
    tipicos = [_payment(payment_id=i, amount=Decimal("50")) for i in range(1, 4)]
    atipico = _payment(payment_id=99, amount=Decimal("200"))

    anomalias = build_payment_anomalies([*tipicos, atipico])

    assert [a.payment_id for a in anomalias] == [99]


def test_sin_suficientes_muestras_no_hay_anomalia() -> None:
    pagos = [
        _payment(payment_id=1, amount=Decimal("50")),
        _payment(payment_id=2, amount=Decimal("500")),
    ]

    assert build_payment_anomalies(pagos) == []


def test_una_emergencia_nunca_es_anomalia() -> None:
    tipicos = [
        _payment(payment_id=i, appointment_type_id=2, is_emergency_type=True, amount=Decimal("50"))
        for i in range(1, 4)
    ]
    atipico = _payment(
        payment_id=99, appointment_type_id=2, is_emergency_type=True, amount=Decimal("500")
    )

    assert build_payment_anomalies([*tipicos, atipico]) == []


def _signal(**overrides: object) -> VeterinarianSignal:
    valores: dict[str, object] = {
        "veterinarian_id": 1,
        "veterinarian_name": "Carla Doe",
        "low_rating_count": 0,
        "complaint_count": 0,
    }
    valores.update(overrides)
    return VeterinarianSignal(**valores)  # type: ignore[arg-type]


def test_alerta_por_reseñas_bajas() -> None:
    señal = _signal(low_rating_count=3)

    assert len(build_veterinarian_alerts([señal])) == 1


def test_alerta_por_reclamos() -> None:
    señal = _signal(complaint_count=2)

    assert len(build_veterinarian_alerts([señal])) == 1


def test_sin_señales_suficientes_no_hay_alerta() -> None:
    señal = _signal(low_rating_count=1, complaint_count=1)

    assert build_veterinarian_alerts([señal]) == []

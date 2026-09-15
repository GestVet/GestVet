"""Pruebas de las reglas del panel de indicadores. Python puro, sin base."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from gestvet.modules.insights.domain.entities import (
    AppointmentRecord,
    PaymentRecord,
    PetCareRecord,
    PetOverviewRecord,
    ServiceConsumptionRecord,
)
from gestvet.modules.insights.domain.rules import (
    build_care_reminders,
    build_no_show_risks,
    build_payment_anomalies,
    build_pet_overview,
    build_service_consumption,
    build_veterinarian_alerts,
    vaccination_status,
)
from gestvet.modules.insights.ports.reputation_directory import VeterinarianSignal

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
HOY = date(2026, 9, 12)


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


def _pet_overview(**overrides: object) -> PetOverviewRecord:
    valores: dict[str, object] = {
        "pet_id": 1,
        "pet_name": "Rocco",
        "owner_id": 2,
        "owner_name": "Ana Quispe",
        "species": "Perro",
        "breed": "Mestizo",
        "sex": "male",
        "birth_date": date(2022, 9, 12),
        "weight_kg": Decimal("12.50"),
        "is_active": True,
        "last_vaccine_on": None,
        "next_vaccine_due_on": None,
        "vaccine_count": 0,
    }
    valores.update(overrides)
    return PetOverviewRecord(**valores)  # type: ignore[arg-type]


def test_sin_vacunas_el_estado_es_sin_vacunas() -> None:
    mascota = _pet_overview(vaccine_count=0)

    assert vaccination_status(mascota, HOY) == "no_vaccines"


def test_proxima_dosis_vencida() -> None:
    mascota = _pet_overview(vaccine_count=1, next_vaccine_due_on=HOY - timedelta(days=1))

    assert vaccination_status(mascota, HOY) == "overdue"


def test_proxima_dosis_dentro_de_30_dias_esta_por_vencer() -> None:
    mascota = _pet_overview(vaccine_count=1, next_vaccine_due_on=HOY + timedelta(days=10))

    assert vaccination_status(mascota, HOY) == "due_soon"


def test_proxima_dosis_lejana_esta_al_dia() -> None:
    mascota = _pet_overview(vaccine_count=1, next_vaccine_due_on=HOY + timedelta(days=200))

    assert vaccination_status(mascota, HOY) == "up_to_date"


def test_vacunas_sin_refuerzo_pendiente_estan_al_dia() -> None:
    mascota = _pet_overview(vaccine_count=1, next_vaccine_due_on=None)

    assert vaccination_status(mascota, HOY) == "up_to_date"


def test_construye_el_panorama_con_la_edad_calculada() -> None:
    mascota = _pet_overview(birth_date=date(2020, 1, 1))

    panorama = build_pet_overview([mascota], date(2026, 1, 1))

    assert panorama[0].age_years == 6
    assert panorama[0].vaccination_status == "no_vaccines"


def _service_record(**overrides: object) -> ServiceConsumptionRecord:
    valores: dict[str, object] = {
        "appointment_type_id": 1,
        "name": "Consulta general",
        "is_emergency": False,
        "price": Decimal("60"),
        "appointment_count": 3,
    }
    valores.update(overrides)
    return ServiceConsumptionRecord(**valores)  # type: ignore[arg-type]


def test_calcula_el_ingreso_estimado_con_el_precio_de_catalogo() -> None:
    servicio = _service_record(price=Decimal("60"), appointment_count=3)

    resultado = build_service_consumption([servicio])

    assert resultado[0].estimated_revenue == Decimal("180")


def test_ordena_por_el_mas_consumido_primero() -> None:
    poco_usado = _service_record(appointment_type_id=1, name="Baño", appointment_count=1)
    muy_usado = _service_record(appointment_type_id=2, name="Consulta", appointment_count=5)

    resultado = build_service_consumption([poco_usado, muy_usado])

    assert [item.name for item in resultado] == ["Consulta", "Baño"]

"""Pruebas del dominio de citas. Python puro, sin base ni servidor."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from gestvet.core.clinic_time import clinic_day_window
from gestvet.modules.appointments.domain.entities import (
    NO_SHOW_GRACE,
    TURNAROUND,
    Appointment,
    AppointmentStatus,
    AppointmentType,
)
from gestvet.modules.appointments.domain.exceptions import IllegalStatusChange, InvalidAppointment

BASE = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)
CLIENTE = 10
VETERINARIO = 20


def _cita(inicio: datetime = BASE, minutos: int = 30, description: str = "") -> Appointment:
    return Appointment(
        scheduled_at=inicio,
        duration=timedelta(minutes=minutos),
        client_id=CLIENTE,
        pet_id=1,
        veterinarian_id=VETERINARIO,
        appointment_type_id=1,
        description=description,
    )


def test_la_fecha_debe_traer_zona_horaria() -> None:
    with pytest.raises(InvalidAppointment):
        _cita(inicio=BASE.replace(tzinfo=None))


def test_la_ventana_ocupada_incluye_el_margen() -> None:
    cita = _cita(minutos=30)

    assert cita.ends_at == BASE + timedelta(minutes=30)
    assert cita.blocked_until == BASE + timedelta(minutes=30) + TURNAROUND


@pytest.mark.parametrize(
    ("desplazamiento_minutos", "pisa"),
    [
        (0, True),
        (20, True),
        (35, True),
        (40, False),
        (-30, True),
        (-45, False),
    ],
)
def test_el_solapamiento_respeta_el_margen(desplazamiento_minutos: int, pisa: bool) -> None:
    """Una cita de 30 minutos bloquea 40: los 30 suyos y los 10 de margen."""
    existente = _cita(minutos=30)
    inicio = BASE + timedelta(minutes=desplazamiento_minutos)

    assert existente.overlaps(inicio, inicio + timedelta(minutes=30)) is pisa


def test_una_cita_recien_creada_queda_pendiente() -> None:
    assert _cita().status is AppointmentStatus.PENDING


def test_el_camino_normal_de_una_cita() -> None:
    cita = _cita()

    cita.confirm(VETERINARIO)
    assert cita.status is AppointmentStatus.CONFIRMED
    assert cita.updated_by == VETERINARIO

    cita.complete(VETERINARIO)
    assert cita.status is AppointmentStatus.COMPLETED
    assert cita.status.is_final


def test_una_pendiente_no_puede_completarse_sin_confirmar() -> None:
    with pytest.raises(IllegalStatusChange):
        _cita().complete(VETERINARIO)


def test_el_personal_marca_la_inasistencia_a_mano() -> None:
    cita = _cita()
    cita.confirm(VETERINARIO)

    cita.mark_no_show(VETERINARIO)

    assert cita.status is AppointmentStatus.NO_SHOW
    assert cita.status.is_final


def test_una_no_asistida_no_revive() -> None:
    cita = _cita()
    cita.confirm(VETERINARIO)
    cita.mark_no_show(VETERINARIO)

    with pytest.raises(IllegalStatusChange):
        cita.complete(VETERINARIO)


def test_una_completada_no_puede_marcarse_como_no_asistida() -> None:
    cita = _cita()
    cita.confirm(VETERINARIO)
    cita.complete(VETERINARIO)

    with pytest.raises(IllegalStatusChange):
        cita.mark_no_show(VETERINARIO)


def test_el_estado_efectivo_es_el_mismo_mientras_no_pase_el_margen() -> None:
    cita = _cita()
    cita.confirm(VETERINARIO)
    momento = cita.ends_at + NO_SHOW_GRACE - timedelta(minutes=1)

    assert cita.effective_status(momento) is AppointmentStatus.CONFIRMED


def test_el_estado_efectivo_pasa_a_no_asistio_tras_el_margen() -> None:
    cita = _cita()
    cita.confirm(VETERINARIO)
    momento = cita.ends_at + NO_SHOW_GRACE

    assert cita.effective_status(momento) is AppointmentStatus.NO_SHOW
    # El cambio es solo de lectura: no reescribe el estado real.
    assert cita.status is AppointmentStatus.CONFIRMED


def test_una_completada_nunca_es_efectivamente_no_asistida() -> None:
    cita = _cita()
    cita.confirm(VETERINARIO)
    cita.complete(VETERINARIO)
    momento = cita.ends_at + NO_SHOW_GRACE * 10

    assert cita.effective_status(momento) is AppointmentStatus.COMPLETED


def test_una_cancelada_no_revive() -> None:
    """El original dejaba pasar cualquier estado a cualquier otro."""
    cita = _cita()
    cita.cancel(CLIENTE, "Se me cruzo un viaje")

    with pytest.raises(IllegalStatusChange):
        cita.confirm(VETERINARIO)
    with pytest.raises(IllegalStatusChange):
        cita.complete(VETERINARIO)


def test_una_completada_no_se_cancela() -> None:
    cita = _cita()
    cita.confirm(VETERINARIO)
    cita.complete(VETERINARIO)

    with pytest.raises(IllegalStatusChange):
        cita.cancel(CLIENTE, "Me arrepenti")


def test_cancelar_exige_una_razon() -> None:
    """Quien cancela le debe una explicacion a la otra parte."""
    with pytest.raises(InvalidAppointment):
        _cita().cancel(CLIENTE, "   ")


def test_la_cancelacion_guarda_razon_y_autor() -> None:
    cita = _cita()

    cita.cancel(CLIENTE, "  Se me cruzo un viaje  ")

    assert cita.status is AppointmentStatus.CANCELLED
    assert cita.cancellation_reason == "Se me cruzo un viaje"
    assert cita.updated_by == CLIENTE


def test_una_cancelada_libera_la_agenda() -> None:
    assert AppointmentStatus.CANCELLED.blocks_the_agenda is False
    assert AppointmentStatus.PENDING.blocks_the_agenda is True
    assert AppointmentStatus.COMPLETED.blocks_the_agenda is True


def test_la_cita_sabe_quien_participa() -> None:
    cita = _cita()

    assert cita.involves(CLIENTE)
    assert cita.involves(VETERINARIO)
    assert not cita.involves(999)


def test_la_descripcion_no_puede_exceder_su_largo() -> None:
    with pytest.raises(InvalidAppointment):
        _cita(description="x" * 501)


def test_un_motivo_necesita_nombre_duracion_y_precio_validos() -> None:
    with pytest.raises(InvalidAppointment):
        AppointmentType(name="  ", duration=timedelta(minutes=30), price=Decimal("10"))
    with pytest.raises(InvalidAppointment):
        AppointmentType(name="Consulta", duration=timedelta(0), price=Decimal("10"))
    with pytest.raises(InvalidAppointment):
        AppointmentType(name="Consulta", duration=timedelta(minutes=30), price=Decimal("-1"))


def test_un_motivo_no_puede_durar_una_jornada_entera() -> None:
    with pytest.raises(InvalidAppointment):
        AppointmentType(name="Consulta", duration=timedelta(hours=9), price=Decimal("10"))


def test_la_ventana_del_dia_de_la_clinica_no_es_el_dia_calendario_utc() -> None:
    """Las 20:00 en Trujillo caen del otro lado de la medianoche en UTC.

    Comparar `.date()` en UTC directamente confundiría esta hora con el día
    calendario siguiente, aunque para la clínica sigue siendo la misma
    jornada.
    """
    noche_en_trujillo = datetime(2026, 9, 13, 22, 0, tzinfo=UTC) + timedelta(hours=5)
    assert noche_en_trujillo.date() == datetime(2026, 9, 14).date()

    manana_en_trujillo = datetime(2026, 9, 13, 8, 0, tzinfo=UTC) + timedelta(hours=5)
    inicio, fin = clinic_day_window(manana_en_trujillo)

    assert inicio <= manana_en_trujillo < fin
    assert inicio <= noche_en_trujillo < fin


def test_la_ventana_del_dia_dura_veinticuatro_horas_y_excluye_los_vecinos() -> None:
    momento = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
    inicio, fin = clinic_day_window(momento)

    assert fin - inicio == timedelta(days=1)
    assert inicio <= momento < fin
    assert momento - timedelta(days=1) < inicio
    assert momento + timedelta(days=1) >= fin

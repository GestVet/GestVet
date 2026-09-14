"""Pruebas del dominio de la agenda."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest

from gestvet.core.clinic_time import clinic_midnight
from gestvet.modules.availability.domain.entities import (
    AvailabilitySlot,
    ChangeRequestStatus,
    ShiftChangeRequest,
    ShiftKind,
    ensure_schedulable,
)
from gestvet.modules.availability.domain.exceptions import (
    ChangeRequestAlreadyResolved,
    InvalidChangeRequest,
    InvalidSlot,
    OverlappingSlot,
)
from gestvet.modules.availability.domain.weekly_plan import WeeklyShift, expand_weekly_plan

# 09:00 en Trujillo.
BASE = datetime(2026, 9, 14, 14, 0, tzinfo=UTC)
LUNES = date(2026, 9, 14)


def _slot(
    inicio: datetime = BASE,
    horas: float = 4,
    vet: int = 1,
    kind: ShiftKind = ShiftKind.REGULAR,
) -> AvailabilitySlot:
    return AvailabilitySlot(
        veterinarian_id=vet, starts_at=inicio, ends_at=inicio + timedelta(hours=horas), kind=kind
    )


def test_el_fin_debe_ser_posterior_al_inicio() -> None:
    with pytest.raises(InvalidSlot):
        AvailabilitySlot(veterinarian_id=1, starts_at=BASE, ends_at=BASE)


def test_un_turno_demasiado_corto_se_rechaza() -> None:
    with pytest.raises(InvalidSlot):
        AvailabilitySlot(veterinarian_id=1, starts_at=BASE, ends_at=BASE + timedelta(minutes=5))


def test_un_turno_de_atencion_de_mas_de_doce_horas_se_rechaza() -> None:
    with pytest.raises(InvalidSlot):
        _slot(inicio=BASE - timedelta(hours=8), horas=13)


def test_un_turno_de_atencion_no_cruza_la_medianoche() -> None:
    """La noche la cubre la guardia."""
    with pytest.raises(InvalidSlot):
        _slot(inicio=BASE + timedelta(hours=11), horas=6)


def test_un_turno_de_atencion_puede_terminar_justo_a_medianoche() -> None:
    assert _slot(inicio=BASE + timedelta(hours=11), horas=4).duration == timedelta(hours=4)


def test_una_guardia_puede_cubrir_la_noche() -> None:
    guardia = _slot(inicio=BASE + timedelta(hours=11), horas=12, kind=ShiftKind.ON_CALL)

    assert guardia.kind is ShiftKind.ON_CALL


def test_una_guardia_no_supera_las_veinticuatro_horas() -> None:
    with pytest.raises(InvalidSlot):
        _slot(horas=25, kind=ShiftKind.ON_CALL)


def test_un_inicio_sin_zona_horaria_se_rechaza() -> None:
    """La ambigüedad en una agenda se paga con citas a la hora equivocada."""
    with pytest.raises(InvalidSlot):
        AvailabilitySlot(
            veterinarian_id=1,
            starts_at=BASE.replace(tzinfo=None),
            ends_at=BASE + timedelta(hours=2),
        )


def test_un_fin_sin_zona_horaria_se_rechaza() -> None:
    with pytest.raises(InvalidSlot):
        AvailabilitySlot(
            veterinarian_id=1,
            starts_at=BASE,
            ends_at=(BASE + timedelta(hours=2)).replace(tzinfo=None),
        )


def test_la_hora_se_normaliza_a_utc() -> None:
    otra_zona = BASE.astimezone(tz=timezone(timedelta(hours=-5)))
    slot = AvailabilitySlot(
        veterinarian_id=1, starts_at=otra_zona, ends_at=otra_zona + timedelta(hours=2)
    )
    assert slot.starts_at.tzinfo is UTC
    assert slot.starts_at == BASE


@pytest.mark.parametrize(
    ("desplazamiento_horas", "se_superpone"),
    [(0, True), (2, True), (4, False), (-4, False), (5, False)],
)
def test_dos_turnos_se_superponen_solo_si_comparten_tiempo(
    desplazamiento_horas: int, se_superpone: bool
) -> None:
    """Compartir el extremo no es superponerse: son contiguos, no simultáneos."""
    uno = _slot()
    otro = _slot(inicio=BASE + timedelta(hours=desplazamiento_horas))

    assert uno.overlaps(otro) is se_superpone
    assert otro.overlaps(uno) is se_superpone


@pytest.mark.parametrize(
    ("inicio_horas", "fin_horas", "cabe"),
    [(0, 4, True), (1, 3, True), (0, 5, False), (-1, 2, False)],
)
def test_una_ventana_cabe_solo_si_entra_entera(
    inicio_horas: int, fin_horas: int, cabe: bool
) -> None:
    assert (
        _slot().covers(BASE + timedelta(hours=inicio_horas), BASE + timedelta(hours=fin_horas))
        is cabe
    )


@pytest.mark.parametrize(
    ("turno", "ahora"),
    [
        # Ya terminó.
        (_slot(), BASE + timedelta(hours=5)),
        # Empieza en un día que ya pasó, aunque todavía no terminó.
        (_slot(inicio=BASE - timedelta(hours=13), horas=15, kind=ShiftKind.ON_CALL), BASE),
        # A más de un año.
        (_slot(inicio=BASE + timedelta(days=400)), BASE),
        # El año 3000.
        (_slot(inicio=datetime(3000, 1, 1, 14, tzinfo=UTC)), BASE),
    ],
)
def test_un_turno_nuevo_es_de_hoy_en_adelante_y_dentro_del_ano(
    turno: AvailabilitySlot, ahora: datetime
) -> None:
    with pytest.raises(InvalidSlot):
        ensure_schedulable(turno, ahora)


def test_un_turno_de_hoy_que_ya_empezo_se_puede_asignar() -> None:
    ensure_schedulable(_slot(), BASE + timedelta(hours=1))


def test_el_horario_semanal_se_expande_en_turnos() -> None:
    plan = [
        WeeklyShift(weekday=0, starts=time(9), ends=time(13)),
        WeeklyShift(weekday=2, starts=time(20), ends=time(8), kind=ShiftKind.ON_CALL),
    ]

    turnos = expand_weekly_plan(7, LUNES, 2, plan, assigned_by=1)

    assert len(turnos) == 4
    primero, guardia = turnos[0], turnos[1]
    assert primero.starts_at == clinic_midnight(LUNES) + timedelta(hours=9)
    assert primero.kind is ShiftKind.REGULAR
    assert guardia.starts_at == clinic_midnight(LUNES + timedelta(days=2)) + timedelta(hours=20)
    # De 20 a 8 termina al día siguiente.
    assert guardia.ends_at == clinic_midnight(LUNES + timedelta(days=3)) + timedelta(hours=8)
    assert {turno.assigned_by for turno in turnos} == {1}


@pytest.mark.parametrize("semanas", [0, 13])
def test_el_horario_se_aplica_de_una_a_doce_semanas(semanas: int) -> None:
    with pytest.raises(InvalidSlot):
        expand_weekly_plan(7, LUNES, semanas, [WeeklyShift(0, time(9), time(13))])


def test_un_horario_sin_dias_se_rechaza() -> None:
    with pytest.raises(InvalidSlot):
        expand_weekly_plan(7, LUNES, 1, [])


def test_un_horario_que_se_pisa_a_si_mismo_se_rechaza() -> None:
    plan = [
        WeeklyShift(weekday=0, starts=time(20), ends=time(8), kind=ShiftKind.ON_CALL),
        WeeklyShift(weekday=1, starts=time(7), ends=time(13)),
    ]

    with pytest.raises(OverlappingSlot):
        expand_weekly_plan(7, LUNES, 1, plan)


def test_un_dia_de_la_semana_fuera_de_rango_se_rechaza() -> None:
    with pytest.raises(InvalidSlot):
        WeeklyShift(weekday=7, starts=time(9), ends=time(13))


def test_un_pedido_de_cambio_explica_que_necesita() -> None:
    with pytest.raises(InvalidChangeRequest):
        ShiftChangeRequest(veterinarian_id=1, message="  no ")


def test_un_pedido_se_responde_una_sola_vez() -> None:
    pedido = ShiftChangeRequest(veterinarian_id=1, message="Tengo control médico el lunes")

    pedido.resolve(actor_id=9, accepted=True, response="Lo cubre Pedro", now=BASE)

    assert pedido.status is ChangeRequestStatus.ACCEPTED
    assert pedido.resolved_by == 9
    with pytest.raises(ChangeRequestAlreadyResolved):
        pedido.resolve(actor_id=9, accepted=False, response="", now=BASE)

"""Pruebas del dominio de disponibilidad."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from gestvet.availability.domain.entities import AvailabilitySlot
from gestvet.availability.domain.exceptions import InvalidSlot

BASE = datetime(2026, 9, 14, 9, 0, tzinfo=UTC)


def _slot(inicio: datetime = BASE, horas: float = 4, vet: int = 1) -> AvailabilitySlot:
    return AvailabilitySlot(
        veterinarian_id=vet, starts_at=inicio, ends_at=inicio + timedelta(hours=horas)
    )


def test_el_fin_debe_ser_posterior_al_inicio() -> None:
    with pytest.raises(InvalidSlot):
        AvailabilitySlot(veterinarian_id=1, starts_at=BASE, ends_at=BASE)


def test_un_tramo_demasiado_corto_se_rechaza() -> None:
    with pytest.raises(InvalidSlot):
        AvailabilitySlot(veterinarian_id=1, starts_at=BASE, ends_at=BASE + timedelta(minutes=5))


def test_un_tramo_demasiado_largo_se_rechaza() -> None:
    with pytest.raises(InvalidSlot):
        _slot(horas=13)


@pytest.mark.parametrize("campo", ["starts_at", "ends_at"])
def test_una_marca_sin_zona_horaria_se_rechaza(campo: str) -> None:
    """La ambigüedad en una agenda se paga con citas a la hora equivocada."""
    datos = {"veterinarian_id": 1, "starts_at": BASE, "ends_at": BASE + timedelta(hours=2)}
    datos[campo] = datos[campo].replace(tzinfo=None)  # type: ignore[union-attr]
    with pytest.raises(InvalidSlot):
        AvailabilitySlot(**datos)  # type: ignore[arg-type]


def test_la_hora_se_normaliza_a_utc() -> None:
    otra_zona = BASE.astimezone(tz=timezone_minus_five())
    slot = AvailabilitySlot(
        veterinarian_id=1, starts_at=otra_zona, ends_at=otra_zona + timedelta(hours=2)
    )
    assert slot.starts_at.tzinfo is UTC
    assert slot.starts_at == BASE


def timezone_minus_five():
    from datetime import timezone

    return timezone(timedelta(hours=-5))


@pytest.mark.parametrize(
    ("desplazamiento_horas", "se_superpone"),
    [
        (0, True),
        (2, True),
        (4, False),
        (-4, False),
        (5, False),
    ],
)
def test_dos_tramos_se_superponen_solo_si_comparten_tiempo(
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

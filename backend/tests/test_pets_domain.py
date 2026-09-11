"""Pruebas del dominio de mascotas. Python puro, sin base ni servidor."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

import pytest

from gestvet.modules.pets.domain.entities import MAX_PLAUSIBLE_AGE_YEARS, Pet
from gestvet.modules.pets.domain.exceptions import InvalidPetData


def _pet(
    name: str = "  Rocco  ",
    species: str = "Perro",
    breed: str = "Mestizo",
    birth_date: date = date(2020, 5, 17),
    owner_id: int = 1,
) -> Pet:
    return Pet(
        name=name,
        species=species,
        breed=breed,
        birth_date=birth_date,
        owner_id=owner_id,
    )


def test_los_textos_se_recortan() -> None:
    assert _pet().name == "Rocco"


@pytest.mark.parametrize(
    "construir",
    [
        lambda: _pet(name="   "),
        lambda: _pet(species="   "),
        lambda: _pet(breed="   "),
    ],
    ids=["nombre", "especie", "raza"],
)
def test_los_textos_obligatorios_no_pueden_venir_vacios(
    construir: Callable[[], Pet],
) -> None:
    with pytest.raises(InvalidPetData):
        construir()


def test_el_nombre_no_puede_exceder_su_largo() -> None:
    with pytest.raises(InvalidPetData):
        _pet(name="x" * 61)


def test_la_fecha_de_nacimiento_no_puede_estar_en_el_futuro() -> None:
    # El dominio mide contra UTC, no contra el reloj local. La prueba usa el
    # mismo reloj: con date.today() pasaba a ser verde o roja segun la hora.
    manana = datetime.now(UTC).date() + timedelta(days=1)
    with pytest.raises(InvalidPetData):
        _pet(birth_date=manana)


def test_una_fecha_inverosimil_se_rechaza() -> None:
    """No es una mascota longeva, es una fecha mal tipeada."""
    with pytest.raises(InvalidPetData):
        hoy = datetime.now(UTC).date()
        _pet(birth_date=hoy.replace(year=hoy.year - MAX_PLAUSIBLE_AGE_YEARS - 1))


@pytest.mark.parametrize(
    ("nacimiento", "hoy", "esperado"),
    [
        (date(2020, 5, 17), date(2026, 5, 17), 6),
        (date(2020, 5, 17), date(2026, 5, 16), 5),
        (date(2020, 5, 17), date(2026, 12, 31), 6),
    ],
)
def test_la_edad_se_calcula_y_no_se_guarda(nacimiento: date, hoy: date, esperado: int) -> None:
    """El original guardaba un numero que envejecia mal."""
    assert _pet(birth_date=nacimiento).age_in_years(today=hoy) == esperado


def test_la_baja_y_el_alta_cambian_el_estado() -> None:
    mascota = _pet()
    mascota.deactivate()
    assert mascota.is_active is False
    mascota.activate()
    assert mascota.is_active is True


def test_la_pertenencia_se_pregunta_a_la_entidad() -> None:
    mascota = _pet(owner_id=7)
    assert mascota.belongs_to(7)
    assert not mascota.belongs_to(8)

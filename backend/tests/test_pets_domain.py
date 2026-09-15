"""Pruebas del dominio de mascotas. Python puro, sin base ni servidor."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from gestvet.modules.pets.domain.entities import (
    MAX_PLAUSIBLE_AGE_YEARS,
    MAX_PLAUSIBLE_HEIGHT_CM,
    MAX_PLAUSIBLE_WEIGHT_KG,
    Pet,
    PetSex,
)
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


def test_el_perfil_del_dueno_queda_vacio_por_defecto() -> None:
    mascota = _pet()

    assert mascota.sex is None
    assert mascota.color == ""
    assert mascota.microchip_number == ""
    assert mascota.temperament == ""


_BIRTH_DATE = date(2020, 5, 17)


def test_el_dueno_actualiza_su_parte_del_perfil() -> None:
    mascota = _pet()

    mascota.update_owner_profile(
        breed="Labrador",
        sex=PetSex.MALE,
        color="Marrón",
        microchip_number="985141000123456",
        temperament="Dócil",
    )

    assert mascota.breed == "Labrador"
    assert mascota.sex is PetSex.MALE
    assert mascota.color == "Marrón"
    assert mascota.microchip_number == "985141000123456"
    assert mascota.temperament == "Dócil"


def test_la_raza_es_obligatoria() -> None:
    mascota = _pet()
    with pytest.raises(InvalidPetData):
        mascota.update_owner_profile(
            breed="   ", sex=None, color="", microchip_number="", temperament=""
        )


def test_el_dueno_tambien_puede_cargar_los_datos_clinicos_al_editar_su_ficha() -> None:
    mascota = _pet()

    mascota.update_owner_profile(
        breed="Mestizo",
        sex=PetSex.FEMALE,
        color="",
        microchip_number="",
        temperament="",
        weight_kg=Decimal("10"),
        height_cm=Decimal("30"),
        is_sterilized=True,
        allergies="Polen",
    )

    assert mascota.weight_kg == Decimal("10")
    assert mascota.height_cm == Decimal("30")
    assert mascota.is_sterilized is True
    assert mascota.allergies == "Polen"


def test_editar_la_ficha_conserva_lo_confirmado_por_el_veterinario_si_se_reenvia() -> None:
    # El formulario del dueño siempre reenvía el estado clínico completo
    # (igual que ya hace con sexo, color o temperamento), así que conservar
    # un dato clínico es responsabilidad de quien llama, no del método.
    mascota = _pet()
    mascota.update_clinical_profile(
        birth_date=_BIRTH_DATE,
        weight_kg=Decimal("10"),
        height_cm=Decimal("30"),
        is_sterilized=True,
        allergies="Polen",
    )

    mascota.update_owner_profile(
        breed="Mestizo",
        sex=PetSex.FEMALE,
        color="",
        microchip_number="",
        temperament="",
        weight_kg=mascota.weight_kg,
        height_cm=mascota.height_cm,
        is_sterilized=mascota.is_sterilized,
        allergies=mascota.allergies,
    )

    assert mascota.weight_kg == Decimal("10")
    assert mascota.is_sterilized is True


def test_el_veterinario_actualiza_el_perfil_clinico() -> None:
    mascota = _pet()

    mascota.update_clinical_profile(
        birth_date=_BIRTH_DATE,
        weight_kg=Decimal("18.5"),
        height_cm=Decimal("45"),
        is_sterilized=False,
        allergies="Ninguna conocida",
    )

    assert mascota.birth_date == _BIRTH_DATE
    assert mascota.weight_kg == Decimal("18.5")
    assert mascota.height_cm == Decimal("45")
    assert mascota.is_sterilized is False
    assert mascota.allergies == "Ninguna conocida"


def test_el_veterinario_no_puede_fijar_una_fecha_de_nacimiento_futura() -> None:
    mascota = _pet()
    with pytest.raises(InvalidPetData):
        mascota.update_clinical_profile(
            birth_date=date(2999, 1, 1),
            weight_kg=None,
            height_cm=None,
            is_sterilized=None,
            allergies="",
        )


@pytest.mark.parametrize("peso", [Decimal("0"), Decimal("-1"), MAX_PLAUSIBLE_WEIGHT_KG + 1])
def test_el_peso_debe_ser_plausible(peso: Decimal) -> None:
    mascota = _pet()
    with pytest.raises(InvalidPetData):
        mascota.update_clinical_profile(
            birth_date=_BIRTH_DATE, weight_kg=peso, height_cm=None, is_sterilized=None, allergies=""
        )


@pytest.mark.parametrize("altura", [Decimal("0"), Decimal("-1"), MAX_PLAUSIBLE_HEIGHT_CM + 1])
def test_la_altura_debe_ser_plausible(altura: Decimal) -> None:
    mascota = _pet()
    with pytest.raises(InvalidPetData):
        mascota.update_clinical_profile(
            birth_date=_BIRTH_DATE,
            weight_kg=None,
            height_cm=altura,
            is_sterilized=None,
            allergies="",
        )


def test_el_texto_libre_del_perfil_clinico_no_puede_exceder_su_largo() -> None:
    mascota = _pet()
    with pytest.raises(InvalidPetData):
        mascota.update_clinical_profile(
            birth_date=_BIRTH_DATE,
            weight_kg=None,
            height_cm=None,
            is_sterilized=None,
            allergies="x" * 301,
        )

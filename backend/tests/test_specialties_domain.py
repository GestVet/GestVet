"""Formato y validación del catálogo de especialidades veterinarias."""

from __future__ import annotations

import pytest

from gestvet.modules.accounts.domain.exceptions import InvalidSpecialty
from gestvet.modules.accounts.domain.specialties import (
    Specialty,
    SpecialtyCategory,
    format_specialty_name,
    specialty_key,
)


@pytest.mark.parametrize(
    ("escrito", "guardado"),
    [
        ("Cardiología veterinaria", "Cardiología veterinaria"),
        ("  Oncología   veterinaria ", "Oncología veterinaria"),
    ],
)
def test_el_nombre_se_recorta_y_colapsa_los_espacios(escrito: str, guardado: str) -> None:
    assert format_specialty_name(escrito) == guardado


@pytest.mark.parametrize("escrito", ["", "  ", "ab", "x" * 81])
def test_un_nombre_invalido_se_rechaza(escrito: str) -> None:
    with pytest.raises(InvalidSpecialty):
        format_specialty_name(escrito)


def test_la_clave_iguala_tildes_mayusculas_y_espacios() -> None:
    assert specialty_key("  Cardiología  Veterinaria ") == specialty_key("cardiologia veterinaria")


def test_una_descripcion_demasiado_larga_se_rechaza() -> None:
    with pytest.raises(InvalidSpecialty):
        Specialty(
            name="Cardiología veterinaria",
            category=SpecialtyCategory.DISCIPLINE,
            description="x" * 241,
        )


def test_actualizar_reemplaza_todos_los_campos() -> None:
    specialty = Specialty(name="Cardiología veterinaria", category=SpecialtyCategory.DISCIPLINE)

    specialty.update(
        name="Cardiología y medicina interna",
        category=SpecialtyCategory.DISCIPLINE,
        description="Corazón y enfermedades crónicas.",
        is_active=False,
    )

    assert specialty.name == "Cardiología y medicina interna"
    assert specialty.description == "Corazón y enfermedades crónicas."
    assert specialty.is_active is False

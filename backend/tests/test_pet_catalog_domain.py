"""El formato único del catálogo de especies y razas."""

from __future__ import annotations

import pytest

from gestvet.modules.pets.domain.catalog import (
    UNKNOWN_BREED,
    Breed,
    breed_sort_key,
    catalog_key,
    format_breed_name,
    format_species_name,
)
from gestvet.modules.pets.domain.exceptions import CatalogEntryLocked, InvalidPetData
from tests.conftest import load_catalog_migration


@pytest.mark.parametrize(
    ("escrito", "guardado"),
    [
        ("PASTOR ALEMÁN", "Pastor alemán"),
        ("pastor alemán", "Pastor alemán"),
        ("Pastor Alemán", "Pastor alemán"),
        ("  golden    retriever ", "Golden retriever"),
        ("perro sin pelo del Perú", "Perro sin pelo del Perú"),
        ("Perro Sin Pelo Del Perú", "Perro sin pelo del perú"),
        ("cavalier King Charles spaniel", "Cavalier King Charles spaniel"),
        ("dachshund (SALCHICHA)", "Dachshund (salchicha)"),
        ("gOLDEN rETRIEVER", "Golden retriever"),
    ],
)
def test_el_nombre_queda_con_mayuscula_solo_al_inicio(escrito: str, guardado: str) -> None:
    assert format_breed_name(escrito) == guardado


@pytest.mark.parametrize("escrito", ["", "  ", "a", "Perro 2", "Gato!", "x" * 61])
def test_un_nombre_invalido_se_rechaza(escrito: str) -> None:
    with pytest.raises(InvalidPetData):
        format_breed_name(escrito)


def test_la_especie_tiene_su_propio_largo_maximo() -> None:
    with pytest.raises(InvalidPetData):
        format_species_name("x" * 41)


def test_la_clave_iguala_tildes_mayusculas_y_espacios() -> None:
    assert catalog_key("  Pastor  Alemán ") == catalog_key("pastor aleman")


def test_sin_especificar_y_mestizo_van_primero_y_otra_raza_al_final() -> None:
    nombres = ["Otra raza", "Beagle", "Mestizo", "Árabe", "Sin especificar"]

    assert sorted(nombres, key=breed_sort_key) == [
        "Sin especificar",
        "Mestizo",
        "Árabe",
        "Beagle",
        "Otra raza",
    ]


def test_sin_especificar_no_se_renombra_ni_se_desactiva() -> None:
    raza = Breed(name=UNKNOWN_BREED, species_id=1)

    with pytest.raises(CatalogEntryLocked):
        raza.update(name="Desconocida", is_active=True)
    with pytest.raises(CatalogEntryLocked):
        raza.update(name=UNKNOWN_BREED, is_active=False)


def test_la_siembra_ya_tiene_el_formato_del_catalogo() -> None:
    """Un nombre sembrado distinto de su versión formateada entraría duplicado al corregirlo."""
    migracion = load_catalog_migration()
    especies = [fila["name"] for fila in migracion.filas_de_especies()]
    razas = [fila["name"] for fila in migracion.filas_de_razas(dict.fromkeys(especies, 1))]

    assert [format_species_name(nombre) for nombre in especies] == especies
    assert [format_breed_name(nombre) for nombre in razas] == razas

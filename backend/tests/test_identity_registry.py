"""Consulta de DNI: RENIEC sin convenio todavía y la regla de coincidencia de nombres."""

from __future__ import annotations

import pytest

from gestvet.core.dni_reniec import get_identity_registry
from gestvet.core.identity_registry import IdentityRegistryUnavailable, PersonName
from gestvet.modules.accounts.domain.identity_match import names_match

JOSE = PersonName(
    first_names="Jose Pedro", paternal_surname="De La Cruz", maternal_surname="Terrones"
)


async def test_sin_convenio_con_reniec_la_verificacion_no_esta_en_uso() -> None:
    registro = get_identity_registry()

    assert registro.available is False
    with pytest.raises(IdentityRegistryUnavailable):
        await registro.lookup("27427864")


@pytest.mark.parametrize(
    ("nombre", "apellido", "coincide"),
    [
        ("José", "de la Cruz Terrones", True),
        ("pedro", "DE LA CRUZ", True),
        ("Jose Pedro", "Cruz", True),
        ("Juan", "De La Cruz", False),
        ("José", "Terrones", False),
        ("", "De La Cruz", False),
    ],
)
def test_el_nombre_escrito_se_compara_sin_tildes_ni_mayusculas(
    nombre: str, apellido: str, coincide: bool
) -> None:
    assert names_match(nombre, apellido, JOSE) is coincide

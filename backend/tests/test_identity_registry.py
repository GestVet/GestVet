"""Consulta de DNI: el adaptador de Factiliza y la regla de coincidencia de nombres."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from gestvet.core.dni_factiliza import FactilizaIdentityRegistry
from gestvet.core.identity_registry import IdentityRegistryUnavailable, PersonName
from gestvet.modules.accounts.domain.identity_match import names_match

JOSE = PersonName(
    first_names="Jose Pedro", paternal_surname="De La Cruz", maternal_surname="Terrones"
)


def _registro(handler: Callable[[httpx.Request], httpx.Response]) -> FactilizaIdentityRegistry:
    return FactilizaIdentityRegistry(
        api_key="clave-de-prueba",
        base_url="https://api.factiliza.test/v1",
        timeout_seconds=5,
        transport=httpx.MockTransport(handler),
    )


async def test_devuelve_solo_nombres_y_apellidos() -> None:
    pedidos: list[httpx.Request] = []

    def responder(request: httpx.Request) -> httpx.Response:
        pedidos.append(request)
        return httpx.Response(
            200,
            json={
                "status": 200,
                "success": True,
                "data": {
                    "numero": "27427864",
                    "nombres": "JOSE PEDRO",
                    "apellido_paterno": "CASTILLO",
                    "apellido_materno": "TERRONES",
                    "direccion": "CASERIO PUÑA",
                },
            },
        )

    persona = await _registro(responder).lookup("27427864")

    assert pedidos[0].url.path == "/v1/dni/info/27427864"
    assert pedidos[0].headers["Authorization"] == "Bearer clave-de-prueba"
    assert persona == PersonName("Jose Pedro", "Castillo", "Terrones")


@pytest.mark.parametrize(
    "respuesta",
    [
        httpx.Response(404, json={"success": False}),
        httpx.Response(200, json={"success": False, "message": "No encontrado"}),
    ],
)
async def test_un_dni_que_no_existe_es_none(respuesta: httpx.Response) -> None:
    assert await _registro(lambda _: respuesta).lookup("00000000") is None


@pytest.mark.parametrize("estado", [401, 429, 500])
async def test_un_fallo_del_proveedor_no_esta_disponible(estado: int) -> None:
    with pytest.raises(IdentityRegistryUnavailable):
        await _registro(lambda _: httpx.Response(estado, json={})).lookup("27427864")


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

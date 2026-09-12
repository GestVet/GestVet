"""Pruebas del adaptador HTTP de la historia clínica.

Recorren la aplicación entera contra una base real, incluida la lectura hacia
la tabla de mascotas para autorizar a un cliente.
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import authorization_for, build_pet, build_user

URL = "/api/v1/medical-records"

ENTRADA = {
    "kind": "consultation",
    "notes": "Buen estado general, sin novedades.",
    "diagnosis": "Sano",
    "treatment": "Ninguno",
    "weight_kg": "12.5",
}


class Escenario:
    def __init__(self, cliente, mascota, veterinario) -> None:
        self.cliente = cliente
        self.mascota = mascota
        self.veterinario = veterinario


async def montar(session: AsyncSession) -> Escenario:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()

    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=cliente.id or 0))
    await session.commit()
    return Escenario(cliente, mascota, veterinario)


async def test_un_veterinario_agrega_una_entrada(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**ENTRADA, "pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["pet_id"] == escenario.mascota.id
    assert body["veterinarian_id"] == escenario.veterinario.id
    assert body["kind"] == "consultation"
    assert body["kind_label"] == "Consulta"
    assert body["weight_kg"] == "12.50"


async def test_un_cliente_no_puede_agregar_una_entrada(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**ENTRADA, "pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_un_veterinario_de_guardia_tambien_agrega_entradas(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    users = SqlAlchemyUserRepository(session)
    guardia = await users.add(build_user("guardia@example.com", role=Role.EMERGENCY_VETERINARIAN))
    await session.commit()

    response = await client.post(
        URL,
        json={**ENTRADA, "pet_id": escenario.mascota.id},
        headers=authorization_for(guardia),
    )

    assert response.status_code == 201


async def test_no_se_puede_agregar_una_entrada_a_una_mascota_inexistente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**ENTRADA, "pet_id": 999},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 404


async def test_las_notas_vacias_no_pasan_la_validacion(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**ENTRADA, "pet_id": escenario.mascota.id, "notes": ""},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 422


async def test_el_dueno_ve_la_historia_de_su_mascota(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await client.post(
        URL,
        json={**ENTRADA, "pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.veterinario),
    )

    response = await client.get(
        URL,
        params={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["notes"] == ENTRADA["notes"]


async def test_un_cliente_no_ve_la_historia_de_una_mascota_ajena(
    client: AsyncClient, session: AsyncSession
) -> None:
    """No se responde 403: decir 'no podés' confirmaría que el id es de alguien."""
    escenario = await montar(session)
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.get(
        URL,
        params={"pet_id": escenario.mascota.id},
        headers=authorization_for(otro),
    )

    assert response.status_code == 404


async def test_el_personal_ve_la_historia_de_cualquier_mascota(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await client.post(
        URL,
        json={**ENTRADA, "pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.veterinario),
    )
    users = SqlAlchemyUserRepository(session)
    otro_vet = await users.add(build_user("otro-vet@example.com", role=Role.VETERINARIAN))
    await session.commit()

    response = await client.get(
        URL,
        params={"pet_id": escenario.mascota.id},
        headers=authorization_for(otro_vet),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_el_filtro_por_tipo(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.veterinario)
    await client.post(URL, json={**ENTRADA, "pet_id": escenario.mascota.id}, headers=cabeceras)
    await client.post(
        URL,
        json={**ENTRADA, "pet_id": escenario.mascota.id, "kind": "vaccine", "notes": "Antirrábica"},
        headers=cabeceras,
    )

    response = await client.get(
        URL,
        params={"pet_id": escenario.mascota.id, "kind": "vaccine"},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["kind"] == "vaccine"


async def test_sin_credencial_no_se_llega_a_ninguna_parte(client: AsyncClient) -> None:
    assert (await client.get(URL, params={"pet_id": 1})).status_code == 401
    assert (await client.post(URL, json={**ENTRADA, "pet_id": 1})).status_code == 401

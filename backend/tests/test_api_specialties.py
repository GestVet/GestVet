"""El catálogo de especialidades y su asignación a los veterinarios."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from tests.conftest import DEFAULT_SPECIALTY_ID, authorization_for, build_user

SPECIALTIES_URL = "/api/v1/specialties"
MANAGE_URL = f"{SPECIALTIES_URL}/manage"
STAFF_URL = "/api/v1/staff"


async def _account(session: AsyncSession, email: str, role: Role) -> User:
    user = await SqlAlchemyUserRepository(session).add(build_user(email, role=role))
    await session.commit()
    return user


async def _admin(session: AsyncSession) -> dict[str, str]:
    return authorization_for(await _account(session, "admin@example.com", Role.ADMIN))


async def test_cualquier_cuenta_ve_el_catalogo_activo(
    client: AsyncClient, session: AsyncSession
) -> None:
    cliente = authorization_for(await _account(session, "ana@example.com", Role.CLIENT))

    response = await client.get(SPECIALTIES_URL, headers=cliente)

    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert all(item["is_active"] for item in body["items"])


async def test_el_catalogo_no_se_ve_sin_credencial(client: AsyncClient) -> None:
    assert (await client.get(SPECIALTIES_URL)).status_code == 401


async def test_solo_la_administracion_agrega_una_especialidad(
    client: AsyncClient, session: AsyncSession
) -> None:
    veterinario = authorization_for(await _account(session, "v@example.com", Role.VETERINARIAN))

    response = await client.post(
        SPECIALTIES_URL,
        json={"name": "Acupuntura veterinaria", "category": "discipline", "description": ""},
        headers=veterinario,
    )

    assert response.status_code == 403


async def test_la_administracion_agrega_una_especialidad(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)

    response = await client.post(
        SPECIALTIES_URL,
        json={
            "name": "Acupuntura veterinaria",
            "category": "discipline",
            "description": "Medicina alternativa.",
        },
        headers=admin,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Acupuntura veterinaria"
    assert body["category"] == "discipline"
    assert body["is_active"] is True


async def test_no_entra_una_especialidad_que_solo_cambia_tildes_o_mayusculas(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)

    response = await client.post(
        SPECIALTIES_URL,
        json={"name": "cardiologia veterinaria", "category": "discipline"},
        headers=admin,
    )

    assert response.status_code == 409


async def test_desactivar_una_especialidad_la_saca_del_catalogo_publico(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)

    response = await client.patch(
        f"{SPECIALTIES_URL}/{DEFAULT_SPECIALTY_ID}",
        json={
            "name": "Cardiología veterinaria",
            "category": "discipline",
            "description": "",
            "is_active": False,
        },
        headers=admin,
    )
    assert response.status_code == 200

    publico = await client.get(SPECIALTIES_URL, headers=admin)
    assert DEFAULT_SPECIALTY_ID not in [item["id"] for item in publico.json()["items"]]

    manejado = await client.get(MANAGE_URL, headers=admin)
    assert DEFAULT_SPECIALTY_ID in [item["id"] for item in manejado.json()["items"]]


async def test_el_alta_de_personal_exige_al_menos_una_especialidad(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)

    response = await client.post(
        STAFF_URL,
        json={
            "email": "carla@example.com",
            "password": "contrasena-larga",
            "first_name": "Carla",
            "last_name": "Blanco",
            "role": Role.VETERINARIAN.value,
            "specialty_ids": [],
        },
        headers=admin,
    )

    assert response.status_code == 422


async def test_el_alta_de_personal_no_acepta_especialidades_inexistentes(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)

    response = await client.post(
        STAFF_URL,
        json={
            "email": "carla@example.com",
            "password": "contrasena-larga",
            "first_name": "Carla",
            "last_name": "Blanco",
            "role": Role.VETERINARIAN.value,
            "specialty_ids": [999999],
        },
        headers=admin,
    )

    assert response.status_code == 422


async def test_la_administracion_reasigna_las_especialidades_de_un_veterinario(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)
    vet = await _account(session, "vet@example.com", Role.VETERINARIAN)

    response = await client.put(
        f"{STAFF_URL}/{vet.id}/specialties",
        json={"specialty_ids": [DEFAULT_SPECIALTY_ID]},
        headers=admin,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == vet.id
    assert [item["id"] for item in body["specialties"]] == [DEFAULT_SPECIALTY_ID]

    listado = await client.get(f"{STAFF_URL}/specialties", headers=admin)
    entrada = next(item for item in listado.json()["items"] if item["user_id"] == vet.id)
    assert [item["id"] for item in entrada["specialties"]] == [DEFAULT_SPECIALTY_ID]


async def test_reasignar_especialidades_a_un_veterinario_sin_ninguna_se_rechaza(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)
    vet = await _account(session, "vet@example.com", Role.VETERINARIAN)

    response = await client.put(
        f"{STAFF_URL}/{vet.id}/specialties",
        json={"specialty_ids": []},
        headers=admin,
    )

    assert response.status_code == 422


async def test_no_se_asignan_especialidades_a_una_cuenta_que_no_es_veterinario(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)
    cliente = await _account(session, "ana@example.com", Role.CLIENT)

    response = await client.put(
        f"{STAFF_URL}/{cliente.id}/specialties",
        json={"specialty_ids": [DEFAULT_SPECIALTY_ID]},
        headers=admin,
    )

    assert response.status_code == 404


async def test_un_veterinario_recien_dado_de_alta_aparece_para_reservar_con_su_especialidad(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _admin(session)

    await client.post(
        STAFF_URL,
        json={
            "email": "carla@example.com",
            "password": "contrasena-larga",
            "first_name": "Carla",
            "last_name": "Blanco",
            "role": Role.VETERINARIAN.value,
            "specialty_ids": [DEFAULT_SPECIALTY_ID],
        },
        headers=admin,
    )

    response = await client.get("/api/v1/veterinarians", headers=admin)

    assert response.status_code == 200
    veterinaria = response.json()["items"][0]
    assert [item["id"] for item in veterinaria["specialties"]] == [DEFAULT_SPECIALTY_ID]

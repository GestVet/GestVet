"""Pruebas del adaptador HTTP de mascotas.

Recorren la aplicación entera: autorización por rol, propiedad del recurso,
validación y traducción de errores de dominio.
"""

from __future__ import annotations

import pytest
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

PETS_URL = "/api/v1/pets"
MINE_URL = f"{PETS_URL}/mine"

NEW_PET = {
    "name": "Rocco",
    "species": "Perro",
    "breed": "Mestizo",
    "birth_date": "2020-05-17",
}


async def _client_account(session: AsyncSession, email: str = "ana@example.com"):
    users = SqlAlchemyUserRepository(session)
    account = await users.add(build_user(email))
    await session.commit()
    return account


async def _staff_account(session: AsyncSession, role: Role = Role.VETERINARIAN):
    users = SqlAlchemyUserRepository(session)
    account = await users.add(build_user(f"{role.value}@example.com", role=role))
    await session.commit()
    return account


async def test_un_cliente_registra_su_mascota(client: AsyncClient, session: AsyncSession) -> None:
    dueno = await _client_account(session)

    response = await client.post(PETS_URL, json=NEW_PET, headers=authorization_for(dueno))

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Rocco"
    assert body["owner_id"] == dueno.id
    assert body["is_active"] is True
    assert body["age_in_years"] >= 6


async def test_el_dueno_lo_fija_el_servidor(client: AsyncClient, session: AsyncSession) -> None:
    """Mandar owner_id en el cuerpo no sirve de nada, igual que con el rol."""
    dueno = await _client_account(session)
    otro = await _client_account(session, "otro@example.com")

    response = await client.post(
        PETS_URL, json={**NEW_PET, "owner_id": otro.id}, headers=authorization_for(dueno)
    )

    assert response.status_code == 201
    assert response.json()["owner_id"] == dueno.id


@pytest.mark.parametrize(
    "campo_invalido",
    [{"name": ""}, {"species": ""}, {"birth_date": "no-es-fecha"}, {"birth_date": "2099-01-01"}],
)
async def test_el_alta_valida_el_cuerpo(
    client: AsyncClient, session: AsyncSession, campo_invalido: dict[str, str]
) -> None:
    dueno = await _client_account(session)

    response = await client.post(
        PETS_URL, json={**NEW_PET, **campo_invalido}, headers=authorization_for(dueno)
    )

    assert response.status_code == 422


async def test_solo_un_cliente_puede_registrar_mascotas(
    client: AsyncClient, session: AsyncSession
) -> None:
    personal = await _staff_account(session)

    response = await client.post(PETS_URL, json=NEW_PET, headers=authorization_for(personal))

    assert response.status_code == 403


async def test_sin_credencial_no_se_llega_a_ninguna_parte(client: AsyncClient) -> None:
    assert (await client.get(MINE_URL)).status_code == 401
    assert (await client.post(PETS_URL, json=NEW_PET)).status_code == 401


async def test_cada_cliente_solo_ve_sus_mascotas(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    beto = await _client_account(session, "beto@example.com")
    pets = SqlAlchemyPetRepository(session)
    await pets.add(build_pet(owner_id=ana.id or 0, name="Rocco"))
    await pets.add(build_pet(owner_id=beto.id or 0, name="Luna"))
    await session.commit()

    response = await client.get(MINE_URL, headers=authorization_for(ana))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Rocco"


async def test_la_baja_de_una_mascota_ajena_responde_que_no_existe(
    client: AsyncClient, session: AsyncSession
) -> None:
    """No se responde 403: decir 'no puedes' confirmaría que el id es de alguien."""
    ana = await _client_account(session)
    beto = await _client_account(session, "beto@example.com")
    pets = SqlAlchemyPetRepository(session)
    ajena = await pets.add(build_pet(owner_id=beto.id or 0))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{ajena.id}/status",
        json={"is_active": False},
        headers=authorization_for(ana),
    )

    assert response.status_code == 404


async def test_la_baja_de_una_mascota_propia_es_definitiva(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Fallecida es un hecho, no un estado administrativo: el dueño no la revierte."""
    ana = await _client_account(session)
    pets = SqlAlchemyPetRepository(session)
    propia = await pets.add(build_pet(owner_id=ana.id or 0))
    await session.commit()
    cabeceras = authorization_for(ana)

    baja = await client.patch(
        f"{PETS_URL}/{propia.id}/status", json={"is_active": False}, headers=cabeceras
    )
    assert baja.status_code == 200
    assert baja.json()["is_active"] is False

    intento_de_alta = await client.patch(
        f"{PETS_URL}/{propia.id}/status", json={"is_active": True}, headers=cabeceras
    )
    assert intento_de_alta.status_code == 409


async def test_el_personal_corrige_un_error_de_carga(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    personal = await _staff_account(session)
    pets = SqlAlchemyPetRepository(session)
    propia = await pets.add(build_pet(owner_id=ana.id or 0, is_active=False))
    await session.commit()

    sin_motivo = await client.patch(
        f"{PETS_URL}/{propia.id}/correct-status",
        json={"is_active": True, "reason": ""},
        headers=authorization_for(personal),
    )
    assert sin_motivo.status_code == 422

    corregida = await client.patch(
        f"{PETS_URL}/{propia.id}/correct-status",
        json={"is_active": True, "reason": "Se cargó como fallecida por error"},
        headers=authorization_for(personal),
    )
    assert corregida.status_code == 200
    assert corregida.json()["is_active"] is True


async def test_un_cliente_no_puede_corregir_el_estado(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    pets = SqlAlchemyPetRepository(session)
    propia = await pets.add(build_pet(owner_id=ana.id or 0, is_active=False))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{propia.id}/correct-status",
        json={"is_active": True, "reason": "Error de carga"},
        headers=authorization_for(ana),
    )
    assert response.status_code == 403


async def test_el_personal_consulta_las_mascotas_de_un_cliente(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    personal = await _staff_account(session)
    pets = SqlAlchemyPetRepository(session)
    await pets.add(build_pet(owner_id=ana.id or 0, name="Rocco"))
    await session.commit()

    response = await client.get(
        f"{PETS_URL}?owner_id={ana.id}", headers=authorization_for(personal)
    )

    assert response.status_code == 200
    assert [item["name"] for item in response.json()["items"]] == ["Rocco"]


async def test_un_cliente_no_puede_espiar_las_mascotas_de_otro(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    beto = await _client_account(session, "beto@example.com")

    response = await client.get(f"{PETS_URL}?owner_id={beto.id}", headers=authorization_for(ana))

    assert response.status_code == 403


async def test_la_busqueda_y_el_filtro_de_estado(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    pets = SqlAlchemyPetRepository(session)
    await pets.add(build_pet(owner_id=ana.id or 0, name="Rocco", species="Perro"))
    await pets.add(build_pet(owner_id=ana.id or 0, name="Luna", species="Gato", is_active=False))
    await session.commit()
    cabeceras = authorization_for(ana)

    por_especie = await client.get(f"{MINE_URL}?search=Gato", headers=cabeceras)
    activas = await client.get(f"{MINE_URL}?is_active=true", headers=cabeceras)

    assert [i["name"] for i in por_especie.json()["items"]] == ["Luna"]
    assert [i["name"] for i in activas.json()["items"]] == ["Rocco"]


async def test_el_dueno_actualiza_el_perfil_que_conoce(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    pets = SqlAlchemyPetRepository(session)
    propia = await pets.add(build_pet(owner_id=ana.id or 0))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{propia.id}/owner-profile",
        json={
            "breed": "Mestizo",
            "sex": "female",
            "color": "Negro con blanco",
            "microchip_number": "985141000123456",
            "temperament": "Juguetona",
        },
        headers=authorization_for(ana),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["breed"] == "Mestizo"
    assert body["sex"] == "female"
    assert body["color"] == "Negro con blanco"
    assert body["microchip_number"] == "985141000123456"
    assert body["temperament"] == "Juguetona"


async def test_un_cliente_no_actualiza_el_perfil_de_una_mascota_ajena(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    beto = await _client_account(session, "beto@example.com")
    pets = SqlAlchemyPetRepository(session)
    ajena = await pets.add(build_pet(owner_id=beto.id or 0))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{ajena.id}/owner-profile",
        json={"breed": "Mestizo", "color": "Negro"},
        headers=authorization_for(ana),
    )

    assert response.status_code == 404


async def test_el_veterinario_actualiza_el_perfil_clinico(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    veterinario = await _staff_account(session)
    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=ana.id or 0))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{mascota.id}/clinical-profile",
        json={
            "birth_date": "2020-05-17",
            "weight_kg": "18.5",
            "height_cm": "45",
            "is_sterilized": True,
            "allergies": "Ninguna conocida",
        },
        headers=authorization_for(veterinario),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["birth_date"] == "2020-05-17"
    assert body["weight_kg"] == "18.50"
    assert body["height_cm"] == "45.00"
    assert body["is_sterilized"] is True
    assert body["allergies"] == "Ninguna conocida"


async def test_un_cliente_no_puede_actualizar_el_perfil_clinico(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    pets = SqlAlchemyPetRepository(session)
    propia = await pets.add(build_pet(owner_id=ana.id or 0))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{propia.id}/clinical-profile",
        json={"birth_date": "2020-05-17", "weight_kg": "10"},
        headers=authorization_for(ana),
    )

    assert response.status_code == 403


async def test_el_admin_no_puede_actualizar_el_perfil_clinico(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Es un acto clínico, igual que agregar una entrada: solo veterinarios."""
    ana = await _client_account(session)
    admin = await _staff_account(session, Role.ADMIN)
    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=ana.id or 0))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{mascota.id}/clinical-profile",
        json={"birth_date": "2020-05-17", "weight_kg": "10"},
        headers=authorization_for(admin),
    )

    assert response.status_code == 403


async def test_el_perfil_clinico_valida_el_peso(client: AsyncClient, session: AsyncSession) -> None:
    ana = await _client_account(session)
    veterinario = await _staff_account(session)
    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=ana.id or 0))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{mascota.id}/clinical-profile",
        json={"birth_date": "2020-05-17", "weight_kg": "-1"},
        headers=authorization_for(veterinario),
    )

    assert response.status_code == 422


async def test_sin_credencial_no_actualiza_ningun_perfil(client: AsyncClient) -> None:
    assert (
        await client.patch(f"{PETS_URL}/1/owner-profile", json={"color": "Negro"})
    ).status_code == 401
    assert (
        await client.patch(f"{PETS_URL}/1/clinical-profile", json={"weight_kg": "10"})
    ).status_code == 401


CATALOG_URL = f"{PETS_URL}/catalog"


async def test_el_catalogo_trae_especies_y_razas_del_peru(
    client: AsyncClient, session: AsyncSession
) -> None:
    dueno = await _client_account(session)

    response = await client.get(CATALOG_URL, headers=authorization_for(dueno))

    assert response.status_code == 200
    especies = {item["name"]: item["breeds"] for item in response.json()["species"]}
    assert "Perro sin pelo del Perú" in especies["Perro"]
    assert "Cuy" in especies["Roedor"]
    assert all("Sin especificar" in razas for razas in especies.values())


async def test_el_catalogo_exige_credencial(client: AsyncClient) -> None:
    assert (await client.get(CATALOG_URL)).status_code == 401


@pytest.mark.parametrize("cambio", [{"species": "Dinosaurio"}, {"breed": "Siamés"}])
async def test_la_especie_y_la_raza_salen_del_catalogo(
    client: AsyncClient, session: AsyncSession, cambio: dict[str, str]
) -> None:
    dueno = await _client_account(session)

    response = await client.post(
        PETS_URL, json={**NEW_PET, **cambio}, headers=authorization_for(dueno)
    )

    assert response.status_code == 422


async def test_el_dueno_completa_la_ficha_de_una_mascota_de_emergencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _client_account(session)
    mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=ana.id or 0, breed="Sin especificar")
    )
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{mascota.id}/owner-profile",
        json={"species": "Gato", "breed": "Siamés", "birth_date": "2022-01-10"},
        headers=authorization_for(ana),
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["species"], body["breed"], body["birth_date"]) == ("Gato", "Siamés", "2022-01-10")


@pytest.mark.parametrize(
    "cambio",
    [
        {"microchip_number": "ABC-123"},
        {"breed": "Siamés"},
        {"birth_date": "2099-01-01"},
    ],
)
async def test_la_ficha_del_dueno_se_valida(
    client: AsyncClient, session: AsyncSession, cambio: dict[str, str]
) -> None:
    ana = await _client_account(session)
    mascota = await SqlAlchemyPetRepository(session).add(build_pet(owner_id=ana.id or 0))
    await session.commit()

    response = await client.patch(
        f"{PETS_URL}/{mascota.id}/owner-profile", json=cambio, headers=authorization_for(ana)
    )

    assert response.status_code == 422

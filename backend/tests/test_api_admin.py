"""Pruebas de la administracion de cuentas.

Alta de personal, listado, activacion, turno de guardia y perfil propio.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from tests.conftest import VALID_PASSWORD, authorization_for, build_user

STAFF_URL = "/api/v1/staff"
USERS_URL = "/api/v1/users"
ME_URL = "/api/v1/auth/me"

NUEVO_VETERINARIO = {
    "email": "carla@example.com",
    "password": VALID_PASSWORD,
    "first_name": "Carla",
    "last_name": "Blanco",
    "role": Role.VETERINARIAN.value,
    "phone": "987654321",
}


async def _cuenta(session: AsyncSession, role: Role, email: str | None = None):
    users = SqlAlchemyUserRepository(session)
    cuenta = await users.add(build_user(email or f"{role.value}@example.com", role=role))
    await session.commit()
    return cuenta


async def test_la_administracion_da_de_alta_un_veterinario(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)

    response = await client.post(STAFF_URL, json=NUEVO_VETERINARIO, headers=authorization_for(jefa))

    assert response.status_code == 201
    assert response.json()["role"] == Role.VETERINARIAN.value


async def test_el_alta_de_personal_no_fabrica_administradores(
    client: AsyncClient, session: AsyncSession
) -> None:
    """La lista de roles asignables no incluye ADMIN."""
    jefa = await _cuenta(session, Role.ADMIN)

    response = await client.post(
        STAFF_URL,
        json={**NUEVO_VETERINARIO, "role": Role.ADMIN.value},
        headers=authorization_for(jefa),
    )

    assert response.status_code == 422


async def test_el_alta_de_personal_no_acepta_el_rol_de_cliente(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)

    response = await client.post(
        STAFF_URL,
        json={**NUEVO_VETERINARIO, "role": Role.CLIENT.value},
        headers=authorization_for(jefa),
    )

    assert response.status_code == 422


@pytest.mark.parametrize("rol", [Role.VETERINARIAN, Role.CLIENT])
async def test_solo_la_administracion_llega_al_alta_de_personal(
    client: AsyncClient, session: AsyncSession, rol: Role
) -> None:
    cuenta = await _cuenta(session, rol, f"{rol.value}@example.com")

    response = await client.post(
        STAFF_URL, json=NUEVO_VETERINARIO, headers=authorization_for(cuenta)
    )

    assert response.status_code == 403


async def test_el_listado_de_personal_excluye_clientes_y_administracion(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    await _cuenta(session, Role.VETERINARIAN, "vet@example.com")
    await _cuenta(session, Role.EMERGENCY_VETERINARIAN, "guardia@example.com")
    await _cuenta(session, Role.CLIENT, "ana@example.com")

    response = await client.get(STAFF_URL, headers=authorization_for(jefa))

    assert response.status_code == 200
    roles = {item["role"] for item in response.json()["items"]}
    assert roles == {Role.VETERINARIAN.value, Role.EMERGENCY_VETERINARIAN.value}


async def test_la_administracion_desactiva_y_reactiva_una_cuenta(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    vet = await _cuenta(session, Role.VETERINARIAN, "vet@example.com")
    cabeceras = authorization_for(jefa)

    baja = await client.patch(
        f"{USERS_URL}/{vet.id}/status", json={"is_active": False}, headers=cabeceras
    )
    assert baja.json()["is_active"] is False

    # Y con la cuenta desactivada, su token deja de servir.
    assert (await client.get(ME_URL, headers=authorization_for(vet))).status_code == 401

    alta = await client.patch(
        f"{USERS_URL}/{vet.id}/status", json={"is_active": True}, headers=cabeceras
    )
    assert alta.json()["is_active"] is True


async def test_nadie_se_desactiva_a_si_mismo(client: AsyncClient, session: AsyncSession) -> None:
    """Dejaria la clinica sin quien reactive la cuenta. El original lo permitia."""
    jefa = await _cuenta(session, Role.ADMIN)

    response = await client.patch(
        f"{USERS_URL}/{jefa.id}/status",
        json={"is_active": False},
        headers=authorization_for(jefa),
    )

    assert response.status_code == 409


async def test_el_turno_de_guardia_se_pone_y_se_saca(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    vet = await _cuenta(session, Role.VETERINARIAN, "vet@example.com")
    cabeceras = authorization_for(jefa)

    puesto = await client.post(f"{STAFF_URL}/{vet.id}/guard-duty", headers=cabeceras)
    sacado = await client.post(f"{STAFF_URL}/{vet.id}/guard-duty", headers=cabeceras)

    assert puesto.json()["role"] == Role.EMERGENCY_VETERINARIAN.value
    assert sacado.json()["role"] == Role.VETERINARIAN.value


@pytest.mark.parametrize("rol", [Role.CLIENT, Role.ADMIN])
async def test_el_turno_de_guardia_no_sirve_para_cambiar_cualquier_rol(
    client: AsyncClient, session: AsyncSession, rol: Role
) -> None:
    """El original aceptaba el rol destino en el cuerpo: servia para todo."""
    jefa = await _cuenta(session, Role.ADMIN)
    otro = await _cuenta(session, rol, f"otro-{rol.value}@example.com")

    response = await client.post(
        f"{STAFF_URL}/{otro.id}/guard-duty", headers=authorization_for(jefa)
    )

    assert response.status_code == 409


async def test_cada_cuenta_edita_su_perfil(client: AsyncClient, session: AsyncSession) -> None:
    ana = await _cuenta(session, Role.CLIENT, "ana@example.com")

    response = await client.patch(
        ME_URL,
        json={"first_name": "Ana Maria", "last_name": "Quispe", "phone": "999888777"},
        headers=authorization_for(ana),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Ana Maria"
    assert body["phone"] == "999888777"
    # Ni el correo ni el rol se tocan desde acá.
    assert body["email"] == "ana@example.com"
    assert body["role"] == Role.CLIENT.value


async def test_cambiar_la_contrasena_deja_acceder_con_la_nueva(
    client: AsyncClient, session: AsyncSession
) -> None:
    ana = await _cuenta(session, Role.CLIENT, "ana@example.com")
    nueva = "otra-contrasena-larga"

    await client.patch(
        ME_URL,
        json={"first_name": "Ana", "last_name": "Quispe", "new_password": nueva},
        headers=authorization_for(ana),
    )

    con_la_nueva = await client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": nueva}
    )
    con_la_vieja = await client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": VALID_PASSWORD}
    )

    assert con_la_nueva.status_code == 200
    assert con_la_vieja.status_code == 401


async def test_el_perfil_no_se_edita_sin_credencial(client: AsyncClient) -> None:
    response = await client.patch(ME_URL, json={"first_name": "X", "last_name": "Y"})

    assert response.status_code == 401


async def test_un_cliente_ve_los_veterinarios_para_reservar(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Necesita el nombre para elegir, no los datos de contacto del personal."""
    ana = await _cuenta(session, Role.CLIENT, "ana@example.com")
    await _cuenta(session, Role.VETERINARIAN, "vet@example.com")
    await _cuenta(session, Role.ADMIN)

    response = await client.get("/api/v1/veterinarians", headers=authorization_for(ana))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert set(body["items"][0]) == {"id", "full_name", "role"}


async def test_los_veterinarios_no_se_listan_sin_credencial(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/veterinarians")).status_code == 401


async def test_una_cuenta_desactivada_no_aparece_para_reservar(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    vet = await _cuenta(session, Role.VETERINARIAN, "vet@example.com")
    await client.patch(
        f"{USERS_URL}/{vet.id}/status",
        json={"is_active": False},
        headers=authorization_for(jefa),
    )

    response = await client.get("/api/v1/veterinarians", headers=authorization_for(jefa))

    assert response.json()["total"] == 0

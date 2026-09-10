"""Pruebas del adaptador HTTP.

Recorren la aplicación entera contra una base real: enrutado, validación de
Pydantic, dependencias, autorización y traducción de errores de dominio a
códigos de estado.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.accounts.adapters.persistence.models import UserRow
from gestvet.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.accounts.domain.entities import Role
from tests.conftest import VALID_PASSWORD, authorization_for, build_user

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CLIENTS_URL = "/api/v1/clients"

NEW_CLIENT = {
    "email": "Ana.Quispe@Example.com",
    "password": VALID_PASSWORD,
    "first_name": "Ana",
    "last_name": "Quispe",
    "phone": "987654321",
}


async def test_el_sondeo_de_vida_responde(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_el_registro_crea_un_cliente(client: AsyncClient) -> None:
    response = await client.post(REGISTER_URL, json=NEW_CLIENT)

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == Role.CLIENT.value
    assert body["email"] == "ana.quispe@example.com"
    assert "password" not in body
    assert "password_hash" not in body


async def test_el_registro_ignora_un_rol_pedido_por_el_cliente(client: AsyncClient) -> None:
    """Cierra el hallazgo P0 de la auditoría, esta vez en el borde HTTP."""
    response = await client.post(REGISTER_URL, json={**NEW_CLIENT, "role": "admin"})

    assert response.status_code == 201
    assert response.json()["role"] == Role.CLIENT.value


async def test_el_registro_rechaza_un_correo_ya_usado(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json=NEW_CLIENT)

    response = await client.post(REGISTER_URL, json=NEW_CLIENT)

    assert response.status_code == 409


@pytest.mark.parametrize(
    "campo_invalido",
    [
        {"password": "corta"},
        {"email": "sin-arroba"},
        {"first_name": ""},
    ],
)
async def test_el_registro_valida_el_cuerpo(
    client: AsyncClient, campo_invalido: dict[str, str]
) -> None:
    response = await client.post(REGISTER_URL, json={**NEW_CLIENT, **campo_invalido})

    assert response.status_code == 422


async def test_el_acceso_devuelve_un_token_utilizable(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json=NEW_CLIENT)

    login = await client.post(
        LOGIN_URL, json={"email": NEW_CLIENT["email"], "password": VALID_PASSWORD}
    )

    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0

    perfil = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert perfil.status_code == 200
    assert perfil.json()["email"] == "ana.quispe@example.com"


@pytest.mark.parametrize(
    "credenciales",
    [
        {"email": "ana.quispe@example.com", "password": "equivocada-larga"},
        {"email": "nadie@example.com", "password": VALID_PASSWORD},
    ],
)
async def test_el_acceso_no_distingue_que_credencial_fallo(
    client: AsyncClient, credenciales: dict[str, str]
) -> None:
    await client.post(REGISTER_URL, json=NEW_CLIENT)

    response = await client.post(LOGIN_URL, json=credenciales)

    assert response.status_code == 401
    assert response.json()["detail"] == "El correo o la contraseña no son correctos."


async def test_el_acceso_valida_el_formato_del_correo(client: AsyncClient) -> None:
    response = await client.post(
        LOGIN_URL, json={"email": "sin-arroba", "password": VALID_PASSWORD}
    )

    assert response.status_code == 422


async def test_una_cuenta_desactivada_no_obtiene_token(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = SqlAlchemyUserRepository(session)
    await users.add(build_user("baja@example.com", is_active=False))
    await session.commit()

    response = await client.post(
        LOGIN_URL, json={"email": "baja@example.com", "password": VALID_PASSWORD}
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "cabeceras",
    [{}, {"Authorization": "Bearer no-es-un-token"}],
)
async def test_el_padron_de_clientes_exige_credencial(
    client: AsyncClient, cabeceras: dict[str, str]
) -> None:
    response = await client.get(CLIENTS_URL, headers=cabeceras)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_un_cliente_no_puede_ver_el_padron(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    await session.commit()

    response = await client.get(CLIENTS_URL, headers=authorization_for(cliente))

    assert response.status_code == 403


@pytest.mark.parametrize(
    "rol",
    [Role.ADMIN, Role.VETERINARIAN, Role.EMERGENCY_VETERINARIAN],
)
async def test_el_personal_de_la_clinica_ve_el_padron(
    client: AsyncClient, session: AsyncSession, rol: Role
) -> None:
    users = SqlAlchemyUserRepository(session)
    await users.add(build_user("ana@example.com"))
    personal = await users.add(build_user(f"{rol.value}@example.com", role=rol))
    await session.commit()

    response = await client.get(CLIENTS_URL, headers=authorization_for(personal))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "ana@example.com"


async def test_una_cuenta_desactivada_pierde_el_acceso_sin_esperar_al_vencimiento(
    client: AsyncClient, session: AsyncSession
) -> None:
    """El rol y el estado se releen de la base, no se creen del token."""
    users = SqlAlchemyUserRepository(session)
    jefa = await users.add(build_user("jefa@example.com", role=Role.ADMIN))
    await session.commit()
    cabeceras = authorization_for(jefa)

    assert (await client.get(CLIENTS_URL, headers=cabeceras)).status_code == 200

    fila = await session.get(UserRow, jefa.id)
    assert fila is not None
    fila.is_active = False
    await session.commit()

    assert (await client.get(CLIENTS_URL, headers=cabeceras)).status_code == 401


async def test_el_padron_acota_el_tamano_de_pagina(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = SqlAlchemyUserRepository(session)
    jefa = await users.add(build_user("jefa@example.com", role=Role.ADMIN))
    await session.commit()

    response = await client.get(f"{CLIENTS_URL}?limit=500", headers=authorization_for(jefa))

    assert response.status_code == 422

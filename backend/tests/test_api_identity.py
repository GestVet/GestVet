"""Verificación de DNI en el registro y consulta de nombres en el alta exprés."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.core.identity_registry import PersonName
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from tests.conftest import (
    VALID_PASSWORD,
    FakeIdentityRegistry,
    authorization_for,
    build_user,
)

REGISTER_URL = "/api/v1/auth/register"
LOOKUP_URL = "/api/v1/clients/document-lookup"
IDENTITY_CHECK_URL = "/api/v1/auth/identity-check"
DNI = "44556677"
MARIA = PersonName(first_names="Maria Elena", paternal_surname="Quispe", maternal_surname="Rojas")
REGISTRO = {
    "email": "maria@example.com",
    "password": VALID_PASSWORD,
    "first_name": "María",
    "last_name": "Quispe Rojas",
    "document_id": DNI,
    "accepts_identity_check": True,
    "accepts_terms": True,
}


async def test_el_registro_verifica_que_el_nombre_sea_el_del_dni(
    client: AsyncClient, identity_registry: FakeIdentityRegistry
) -> None:
    identity_registry.people = {DNI: MARIA}

    response = await client.post(REGISTER_URL, json=REGISTRO)

    assert response.status_code == 201
    assert identity_registry.lookups == [DNI]


async def test_un_nombre_que_no_es_el_del_dni_se_rechaza(
    client: AsyncClient, identity_registry: FakeIdentityRegistry
) -> None:
    identity_registry.people = {DNI: PersonName("Juan", "Perez", "Diaz")}

    response = await client.post(REGISTER_URL, json=REGISTRO)

    assert response.status_code == 422
    # El error no dice a quién pertenece el DNI.
    assert "Juan" not in response.text
    assert "Perez" not in response.text


async def test_un_dni_que_no_existe_se_rechaza(
    client: AsyncClient, identity_registry: FakeIdentityRegistry
) -> None:
    identity_registry.people = {}

    response = await client.post(REGISTER_URL, json=REGISTRO)

    assert response.status_code == 422


async def test_sin_proveedor_disponible_el_registro_sigue(client: AsyncClient) -> None:
    response = await client.post(REGISTER_URL, json=REGISTRO)

    assert response.status_code == 201


async def test_sin_verificacion_en_uso_no_se_pide_autorizacion(client: AsyncClient) -> None:
    estado = await client.get(IDENTITY_CHECK_URL)
    response = await client.post(REGISTER_URL, json={**REGISTRO, "accepts_identity_check": False})

    assert estado.json() == {"available": False}
    assert response.status_code == 201


async def test_con_verificacion_en_uso_el_registro_lo_anuncia(
    client: AsyncClient, identity_registry: FakeIdentityRegistry
) -> None:
    identity_registry.people = {}

    response = await client.get(IDENTITY_CHECK_URL)

    assert response.json() == {"available": True}


async def test_sin_autorizacion_no_hay_registro(
    client: AsyncClient, identity_registry: FakeIdentityRegistry
) -> None:
    identity_registry.people = {DNI: MARIA}

    response = await client.post(REGISTER_URL, json={**REGISTRO, "accepts_identity_check": False})

    assert response.status_code == 422
    assert identity_registry.lookups == []


async def _cuenta(session: AsyncSession, email: str, role: Role):
    user = await SqlAlchemyUserRepository(session).add(build_user(email, role=role))
    await session.commit()
    return user


async def test_el_personal_completa_nombres_por_dni_y_queda_en_movimientos(
    client: AsyncClient, session: AsyncSession, identity_registry: FakeIdentityRegistry
) -> None:
    identity_registry.people = {DNI: MARIA}
    veterinario = await _cuenta(session, "vet@example.com", Role.VETERINARIAN)
    jefa = await _cuenta(session, "jefa@example.com", Role.ADMIN)

    response = await client.post(
        LOOKUP_URL,
        json={"document_id": DNI, "consent": True},
        headers=authorization_for(veterinario),
    )
    bitacora = await client.get("/api/v1/activity", headers=authorization_for(jefa))

    assert response.status_code == 200
    assert response.json() == {"first_names": "Maria Elena", "last_names": "Quispe Rojas"}
    asiento = next(
        item for item in bitacora.json()["items"] if item["kind"] == "document_looked_up"
    )
    assert DNI not in asiento["detail"]


async def test_un_cliente_no_consulta_dnis(client: AsyncClient, session: AsyncSession) -> None:
    cliente = await _cuenta(session, "ana@example.com", Role.CLIENT)

    response = await client.post(
        LOOKUP_URL, json={"document_id": DNI, "consent": True}, headers=authorization_for(cliente)
    )

    assert response.status_code == 403


async def test_sin_proveedor_la_consulta_responde_503(
    client: AsyncClient, session: AsyncSession
) -> None:
    veterinario = await _cuenta(session, "vet@example.com", Role.VETERINARIAN)

    response = await client.post(
        LOOKUP_URL,
        json={"document_id": DNI, "consent": True},
        headers=authorization_for(veterinario),
    )

    assert response.status_code == 503


async def test_un_dni_que_no_existe_responde_404(
    client: AsyncClient, session: AsyncSession, identity_registry: FakeIdentityRegistry
) -> None:
    identity_registry.people = {}
    veterinario = await _cuenta(session, "vet@example.com", Role.VETERINARIAN)

    response = await client.post(
        LOOKUP_URL,
        json={"document_id": DNI, "consent": True},
        headers=authorization_for(veterinario),
    )

    assert response.status_code == 404

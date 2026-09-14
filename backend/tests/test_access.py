"""Pruebas de roles y permisos editables.

Recorren la API entera: quién administra los roles, que un permiso quitado o
dado cambie de verdad lo que la cuenta puede hacer, y las protecciones que
evitan que la administración se quede afuera.
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.core.permissions import SYSTEM_ROLE_PERMISSIONS, Permission
from gestvet.core.realtime import PERMISSIONS_TOPIC
from gestvet.core.realtime_broker import LocalBroker
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from tests.conftest import SYSTEM_ROLE_IDS, authorization_for, build_user

ACCESS_URL = "/api/v1/access"
ROLES_URL = f"{ACCESS_URL}/roles"
CLIENTS_URL = "/api/v1/clients"


async def _account(session: AsyncSession, role: Role) -> User:
    account = await SqlAlchemyUserRepository(session).add(
        build_user(f"{role.value}@example.com", role=role)
    )
    await session.commit()
    return account


def _permissions_of(kind: Role) -> list[str]:
    return sorted(permission.value for permission in SYSTEM_ROLE_PERMISSIONS[kind])


async def _create_role(
    client: AsyncClient, admin: User, kind: Role, permissions: list[str], name: str = "Recepción"
) -> dict:
    response = await client.post(
        ROLES_URL,
        json={"name": name, "account_kind": kind.value, "permissions": permissions},
        headers=authorization_for(admin),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_la_administracion_ve_los_roles_de_sistema(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _account(session, Role.ADMIN)

    response = await client.get(ROLES_URL, headers=authorization_for(admin))

    assert response.status_code == 200
    roles = {item["account_kind"]: item for item in response.json()["items"]}
    assert set(roles) == {kind.value for kind in Role}
    assert all(item["is_system"] for item in roles.values())
    assert roles["client"]["permissions"] == _permissions_of(Role.CLIENT)


async def test_el_catalogo_dice_que_tipos_de_cuenta_pueden_tener_cada_permiso(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _account(session, Role.ADMIN)

    response = await client.get(f"{ACCESS_URL}/permissions", headers=authorization_for(admin))

    assert response.status_code == 200
    items = {item["code"]: item for item in response.json()["items"]}
    assert set(items) == {permission.value for permission in Permission}
    assert items["roles.manage"]["account_kinds"] == ["admin"]


async def test_un_cliente_no_administra_roles(client: AsyncClient, session: AsyncSession) -> None:
    cliente = await _account(session, Role.CLIENT)

    response = await client.get(ROLES_URL, headers=authorization_for(cliente))

    assert response.status_code == 403


async def test_el_perfil_propio_trae_el_rol_y_sus_permisos(
    client: AsyncClient, session: AsyncSession
) -> None:
    veterinario = await _account(session, Role.VETERINARIAN)

    response = await client.get("/api/v1/auth/me", headers=authorization_for(veterinario))

    assert response.status_code == 200
    body = response.json()
    assert body["access_role_name"] == "Veterinario"
    assert body["access_role_id"] == SYSTEM_ROLE_IDS[Role.VETERINARIAN]
    assert body["permissions"] == _permissions_of(Role.VETERINARIAN)


async def test_asignar_un_rol_propio_cambia_lo_que_la_cuenta_puede_hacer(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _account(session, Role.ADMIN)
    veterinario = await _account(session, Role.VETERINARIAN)
    assert (await client.get(CLIENTS_URL, headers=authorization_for(veterinario))).is_success

    sin_padron = [code for code in _permissions_of(Role.VETERINARIAN) if code != "clients.read"]
    rol = await _create_role(client, admin, Role.VETERINARIAN, sin_padron)
    asignado = await client.put(
        f"{ACCESS_URL}/users/{veterinario.id}/role",
        json={"role_id": rol["id"]},
        headers=authorization_for(admin),
    )

    assert asignado.status_code == 204
    denegado = await client.get(CLIENTS_URL, headers=authorization_for(veterinario))
    assert denegado.status_code == 403
    perfil = (await client.get("/api/v1/auth/me", headers=authorization_for(veterinario))).json()
    assert perfil["access_role_name"] == "Recepción"


async def test_volver_al_rol_de_sistema_devuelve_los_permisos(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _account(session, Role.ADMIN)
    veterinario = await _account(session, Role.VETERINARIAN)
    rol = await _create_role(client, admin, Role.VETERINARIAN, ["appointments.read"])
    url = f"{ACCESS_URL}/users/{veterinario.id}/role"
    await client.put(url, json={"role_id": rol["id"]}, headers=authorization_for(admin))

    response = await client.put(url, json={"role_id": None}, headers=authorization_for(admin))

    assert response.status_code == 204
    assert (await client.get(CLIENTS_URL, headers=authorization_for(veterinario))).is_success


async def test_un_permiso_ajeno_al_tipo_de_cuenta_se_rechaza(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _account(session, Role.ADMIN)

    response = await client.post(
        ROLES_URL,
        json={"name": "Cliente VIP", "account_kind": "client", "permissions": ["roles.manage"]},
        headers=authorization_for(admin),
    )

    assert response.status_code == 422


async def test_el_rol_de_administracion_no_pierde_administrar_roles(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _account(session, Role.ADMIN)
    sin_roles = [code for code in _permissions_of(Role.ADMIN) if code != "roles.manage"]

    response = await client.patch(
        f"{ROLES_URL}/{SYSTEM_ROLE_IDS[Role.ADMIN]}",
        json={"name": "Administración", "permissions": sin_roles},
        headers=authorization_for(admin),
    )

    assert response.status_code == 409


async def test_un_rol_de_sistema_no_se_borra_ni_se_renombra(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _account(session, Role.ADMIN)
    url = f"{ROLES_URL}/{SYSTEM_ROLE_IDS[Role.CLIENT]}"

    borrado = await client.delete(url, headers=authorization_for(admin))
    renombrado = await client.patch(
        url,
        json={"name": "Dueños", "permissions": _permissions_of(Role.CLIENT)},
        headers=authorization_for(admin),
    )

    assert borrado.status_code == 409
    assert renombrado.status_code == 409


async def test_un_rol_en_uso_no_se_borra(client: AsyncClient, session: AsyncSession) -> None:
    admin = await _account(session, Role.ADMIN)
    veterinario = await _account(session, Role.VETERINARIAN)
    rol = await _create_role(client, admin, Role.VETERINARIAN, ["appointments.read"])
    await client.put(
        f"{ACCESS_URL}/users/{veterinario.id}/role",
        json={"role_id": rol["id"]},
        headers=authorization_for(admin),
    )

    en_uso = await client.delete(f"{ROLES_URL}/{rol['id']}", headers=authorization_for(admin))

    assert en_uso.status_code == 409


async def test_un_rol_sin_uso_se_borra(client: AsyncClient, session: AsyncSession) -> None:
    admin = await _account(session, Role.ADMIN)
    rol = await _create_role(client, admin, Role.VETERINARIAN, ["appointments.read"])

    response = await client.delete(f"{ROLES_URL}/{rol['id']}", headers=authorization_for(admin))

    assert response.status_code == 204


async def test_nadie_cambia_su_propio_rol(client: AsyncClient, session: AsyncSession) -> None:
    admin = await _account(session, Role.ADMIN)
    rol = await _create_role(client, admin, Role.ADMIN, ["roles.manage"], name="Soporte")

    response = await client.put(
        f"{ACCESS_URL}/users/{admin.id}/role",
        json={"role_id": rol["id"]},
        headers=authorization_for(admin),
    )

    assert response.status_code == 409


async def test_un_rol_solo_se_asigna_a_su_tipo_de_cuenta(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin = await _account(session, Role.ADMIN)
    cliente = await _account(session, Role.CLIENT)
    rol = await _create_role(client, admin, Role.VETERINARIAN, ["appointments.read"])

    response = await client.put(
        f"{ACCESS_URL}/users/{cliente.id}/role",
        json={"role_id": rol["id"]},
        headers=authorization_for(admin),
    )

    assert response.status_code == 422


async def test_el_nombre_de_un_rol_no_se_repite(client: AsyncClient, session: AsyncSession) -> None:
    admin = await _account(session, Role.ADMIN)

    response = await client.post(
        ROLES_URL,
        json={"name": "Cliente", "account_kind": "client", "permissions": []},
        headers=authorization_for(admin),
    )

    assert response.status_code == 409


async def test_cambiar_un_rol_de_sistema_avisa_a_su_tipo_de_cuenta(
    client: AsyncClient, session: AsyncSession, broker: LocalBroker
) -> None:
    admin = await _account(session, Role.ADMIN)
    sin_resenas = [code for code in _permissions_of(Role.CLIENT) if code != "reviews.submit"]

    async with broker.subscribe() as queue:
        response = await client.patch(
            f"{ROLES_URL}/{SYSTEM_ROLE_IDS[Role.CLIENT]}",
            json={"name": "Cliente", "permissions": sin_resenas},
            headers=authorization_for(admin),
        )
        event = queue.get_nowait()

    assert response.status_code == 200
    assert event.topic == PERMISSIONS_TOPIC
    assert event.roles == frozenset({Role.CLIENT})


async def test_asignar_un_rol_avisa_a_la_cuenta(
    client: AsyncClient, session: AsyncSession, broker: LocalBroker
) -> None:
    admin = await _account(session, Role.ADMIN)
    veterinario = await _account(session, Role.VETERINARIAN)
    rol = await _create_role(client, admin, Role.VETERINARIAN, ["appointments.read"])

    async with broker.subscribe() as queue:
        await client.put(
            f"{ACCESS_URL}/users/{veterinario.id}/role",
            json={"role_id": rol["id"]},
            headers=authorization_for(admin),
        )
        event = queue.get_nowait()

    assert event.topic == PERMISSIONS_TOPIC
    assert event.user_ids == frozenset({veterinario.id})

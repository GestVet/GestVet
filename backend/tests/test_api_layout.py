"""Pruebas del API para las preferencias de interfaz (sidebar y dashboard).

Cubre:
- Sin sesión: 401 en GET, PUT y DELETE.
- GET vacío si nunca se guardó nada (listas vacías y updated_at null).
- PUT y GET (upsert).
- 422 por duplicados, patrón inválido o límite de 50 elementos.
- DELETE (204 y posterior GET vacío).
- Aislamiento entre usuarios y compatibilidad con todos los roles (admin, veterinario, cliente).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from tests.conftest import authorization_for, build_user

LAYOUT_URL = "/api/v1/auth/me/layout"


@pytest.mark.parametrize(
    "metodo,kwargs",
    [
        ("get", {}),
        ("put", {"json": {"sidebar_order": ["/panel"], "dashboard_blocks": []}}),
        ("delete", {}),
    ],
)
async def test_layout_exige_sesion(
    client: AsyncClient, metodo: str, kwargs: dict[str, object]
) -> None:
    http_method = getattr(client, metodo)
    response = await http_method(LAYOUT_URL, **kwargs)

    assert response.status_code == 401


async def test_layout_token_invalido_responde_401(client: AsyncClient) -> None:
    headers = {"Authorization": "Bearer token-invalido"}
    response = await client.get(LAYOUT_URL, headers=headers)

    assert response.status_code == 401


async def test_get_layout_retorna_vacio_si_nunca_guardo(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("cliente1@example.com", role=Role.CLIENT))
    await session.commit()

    response = await client.get(LAYOUT_URL, headers=authorization_for(user))

    assert response.status_code == 200
    body = response.json()
    assert body["sidebar_order"] == []
    assert body["dashboard_blocks"] == []
    assert body["updated_at"] is None


async def test_put_y_get_layout_exitoso(client: AsyncClient, session: AsyncSession) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("vet1@example.com", role=Role.VETERINARIAN))
    await session.commit()

    payload = {
        "sidebar_order": ["/panel", "/citas", "/mascotas"],
        "dashboard_blocks": [
            {"id": "/panel/citas-hoy", "visible": True},
            {"id": "/panel/estadisticas", "visible": False},
        ],
    }

    put_response = await client.put(LAYOUT_URL, json=payload, headers=authorization_for(user))
    assert put_response.status_code == 200
    put_body = put_response.json()
    assert put_body["sidebar_order"] == ["/panel", "/citas", "/mascotas"]
    assert put_body["dashboard_blocks"] == [
        {"id": "/panel/citas-hoy", "visible": True},
        {"id": "/panel/estadisticas", "visible": False},
    ]
    assert put_body["updated_at"] is not None

    get_response = await client.get(LAYOUT_URL, headers=authorization_for(user))
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["sidebar_order"] == put_body["sidebar_order"]
    assert get_body["dashboard_blocks"] == put_body["dashboard_blocks"]
    assert get_body["updated_at"] == put_body["updated_at"]


async def test_put_actualiza_layout_existente_upsert(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("admin1@example.com", role=Role.ADMIN))
    await session.commit()

    primer_payload = {
        "sidebar_order": ["/panel"],
        "dashboard_blocks": [{"id": "/panel/resumen", "visible": True}],
    }
    primer_res = await client.put(LAYOUT_URL, json=primer_payload, headers=authorization_for(user))
    assert primer_res.status_code == 200

    segundo_payload = {
        "sidebar_order": ["/personal", "/panel"],
        "dashboard_blocks": [{"id": "/panel/resumen", "visible": False}],
    }
    segundo_res = await client.put(
        LAYOUT_URL, json=segundo_payload, headers=authorization_for(user)
    )
    assert segundo_res.status_code == 200
    segundo_body = segundo_res.json()
    assert segundo_body["sidebar_order"] == ["/personal", "/panel"]
    assert segundo_body["dashboard_blocks"][0]["visible"] is False


@pytest.mark.parametrize(
    "payload_invalido",
    [
        # Duplicado en sidebar_order
        {
            "sidebar_order": ["/panel", "/citas", "/panel"],
            "dashboard_blocks": [],
        },
        # Duplicado en dashboard_blocks
        {
            "sidebar_order": ["/panel"],
            "dashboard_blocks": [
                {"id": "/panel/stats", "visible": True},
                {"id": "/panel/stats", "visible": False},
            ],
        },
        # Patrón inválido en sidebar_order (mayúsculas)
        {
            "sidebar_order": ["/Panel"],
            "dashboard_blocks": [],
        },
        # Patrón inválido en sidebar_order (cadena vacía)
        {
            "sidebar_order": [""],
            "dashboard_blocks": [],
        },
        # Patrón inválido en sidebar_order (espacios)
        {
            "sidebar_order": ["/panel con espacios"],
            "dashboard_blocks": [],
        },
        # Patrón inválido en dashboard_blocks
        {
            "sidebar_order": [],
            "dashboard_blocks": [{"id": "INVALIDO!", "visible": True}],
        },
        # Límite excedido en sidebar_order (51 elementos)
        {
            "sidebar_order": [f"/ruta/{i}" for i in range(51)],
            "dashboard_blocks": [],
        },
        # Límite excedido en dashboard_blocks (51 elementos)
        {
            "sidebar_order": [],
            "dashboard_blocks": [{"id": f"/bloque/{i}", "visible": True} for i in range(51)],
        },
    ],
)
async def test_put_layout_validaciones_422(
    client: AsyncClient, session: AsyncSession, payload_invalido: dict[str, object]
) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("valida@example.com", role=Role.CLIENT))
    await session.commit()

    response = await client.put(LAYOUT_URL, json=payload_invalido, headers=authorization_for(user))
    assert response.status_code == 422


async def test_delete_layout_restablece_preferencias(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("reset@example.com", role=Role.CLIENT))
    await session.commit()

    await client.put(
        LAYOUT_URL,
        json={"sidebar_order": ["/panel"], "dashboard_blocks": []},
        headers=authorization_for(user),
    )

    del_res = await client.delete(LAYOUT_URL, headers=authorization_for(user))
    assert del_res.status_code == 204

    get_res = await client.get(LAYOUT_URL, headers=authorization_for(user))
    assert get_res.status_code == 200
    assert get_res.json() == {
        "sidebar_order": [],
        "dashboard_blocks": [],
        "updated_at": None,
    }


async def test_delete_layout_idempotente_sin_datos_previos(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = SqlAlchemyUserRepository(session)
    user = await users.add(build_user("nuevo_reset@example.com", role=Role.VETERINARIAN))
    await session.commit()

    del_res = await client.delete(LAYOUT_URL, headers=authorization_for(user))
    assert del_res.status_code == 204


async def test_aislamiento_entre_usuarios_y_distintos_roles(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = SqlAlchemyUserRepository(session)
    admin = await users.add(build_user("admin@example.com", role=Role.ADMIN))
    vet = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    client_user = await users.add(build_user("cliente@example.com", role=Role.CLIENT))
    await session.commit()

    admin_headers = authorization_for(admin)
    vet_headers = authorization_for(vet)
    client_headers = authorization_for(client_user)

    # Admin guarda su layout
    await client.put(
        LAYOUT_URL,
        json={
            "sidebar_order": ["/admin/panel", "/admin/usuarios"],
            "dashboard_blocks": [{"id": "/admin/metricas", "visible": True}],
        },
        headers=admin_headers,
    )

    # Vet guarda un layout diferente
    await client.put(
        LAYOUT_URL,
        json={
            "sidebar_order": ["/vet/agenda", "/vet/pacientes"],
            "dashboard_blocks": [{"id": "/vet/turnos", "visible": False}],
        },
        headers=vet_headers,
    )

    # Cliente no guardó nada: debe ver vacío
    client_res = await client.get(LAYOUT_URL, headers=client_headers)
    assert client_res.json()["sidebar_order"] == []
    assert client_res.json()["updated_at"] is None

    # Admin consulta su layout: no se contamina con el del vet
    admin_res = await client.get(LAYOUT_URL, headers=admin_headers)
    assert admin_res.json()["sidebar_order"] == ["/admin/panel", "/admin/usuarios"]
    assert admin_res.json()["dashboard_blocks"][0]["id"] == "/admin/metricas"

    # Vet consulta su layout: no se contamina con el del admin
    vet_res = await client.get(LAYOUT_URL, headers=vet_headers)
    assert vet_res.json()["sidebar_order"] == ["/vet/agenda", "/vet/pacientes"]
    assert vet_res.json()["dashboard_blocks"][0]["id"] == "/vet/turnos"

    # Vet restablece su layout: no afecta al admin
    await client.delete(LAYOUT_URL, headers=vet_headers)
    vet_after_del = await client.get(LAYOUT_URL, headers=vet_headers)
    assert vet_after_del.json()["sidebar_order"] == []

    admin_after_del = await client.get(LAYOUT_URL, headers=admin_headers)
    assert admin_after_del.json()["sidebar_order"] == ["/admin/panel", "/admin/usuarios"]

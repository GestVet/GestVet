"""Pruebas del adaptador HTTP de disponibilidad."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from tests.conftest import authorization_for, build_user

URL = "/api/v1/availability"
MINE_URL = f"{URL}/mine"
BASE = datetime(2026, 9, 14, 9, 0, tzinfo=UTC)


def _tramo(inicio: datetime = BASE, horas: int = 4) -> dict[str, str]:
    return {
        "starts_at": inicio.isoformat(),
        "ends_at": (inicio + timedelta(hours=horas)).isoformat(),
    }


async def _account(session: AsyncSession, role: Role, email: str | None = None):
    users = SqlAlchemyUserRepository(session)
    account = await users.add(build_user(email or f"{role.value}@example.com", role=role))
    await session.commit()
    return account


async def test_un_veterinario_publica_su_agenda(client: AsyncClient, session: AsyncSession) -> None:
    vet = await _account(session, Role.VETERINARIAN)

    response = await client.post(URL, json=_tramo(), headers=authorization_for(vet))

    assert response.status_code == 201
    body = response.json()
    assert body["veterinarian_id"] == vet.id
    assert body["duration_minutes"] == 240


async def test_un_cliente_no_publica_agenda(client: AsyncClient, session: AsyncSession) -> None:
    cliente = await _account(session, Role.CLIENT, "ana@example.com")

    response = await client.post(URL, json=_tramo(), headers=authorization_for(cliente))

    assert response.status_code == 403


async def test_un_tramo_superpuesto_se_rechaza(client: AsyncClient, session: AsyncSession) -> None:
    """El original dejaba publicarlos y la agenda ofrecía dos veces la misma hora."""
    vet = await _account(session, Role.VETERINARIAN)
    cabeceras = authorization_for(vet)
    await client.post(URL, json=_tramo(), headers=cabeceras)

    response = await client.post(
        URL, json=_tramo(inicio=BASE + timedelta(hours=2)), headers=cabeceras
    )

    assert response.status_code == 409


async def test_un_tramo_contiguo_si_se_acepta(client: AsyncClient, session: AsyncSession) -> None:
    vet = await _account(session, Role.VETERINARIAN)
    cabeceras = authorization_for(vet)
    await client.post(URL, json=_tramo(), headers=cabeceras)

    response = await client.post(
        URL, json=_tramo(inicio=BASE + timedelta(hours=4)), headers=cabeceras
    )

    assert response.status_code == 201


async def test_dos_veterinarios_pueden_coincidir_en_horario(
    client: AsyncClient, session: AsyncSession
) -> None:
    uno = await _account(session, Role.VETERINARIAN, "uno@example.com")
    otro = await _account(session, Role.VETERINARIAN, "otro@example.com")
    await client.post(URL, json=_tramo(), headers=authorization_for(uno))

    response = await client.post(URL, json=_tramo(), headers=authorization_for(otro))

    assert response.status_code == 201


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"starts_at": BASE.isoformat(), "ends_at": BASE.isoformat()},
        {"starts_at": "2026-09-14T09:00:00", "ends_at": "2026-09-14T13:00:00"},
        _tramo(horas=13),
    ],
)
async def test_el_cuerpo_se_valida(
    client: AsyncClient, session: AsyncSession, cuerpo: dict[str, str]
) -> None:
    vet = await _account(session, Role.VETERINARIAN)

    response = await client.post(URL, json=cuerpo, headers=authorization_for(vet))

    assert response.status_code == 422


async def test_un_cliente_consulta_la_agenda_de_un_veterinario(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Necesita verla para poder reservar."""
    vet = await _account(session, Role.VETERINARIAN)
    cliente = await _account(session, Role.CLIENT, "ana@example.com")
    await client.post(URL, json=_tramo(), headers=authorization_for(vet))

    response = await client.get(
        URL, params={"veterinarian_id": vet.id}, headers=authorization_for(cliente)
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_la_agenda_no_se_consulta_sin_credencial(client: AsyncClient) -> None:
    assert (await client.get(f"{URL}?veterinarian_id=1")).status_code == 401


async def test_retirar_un_tramo_propio_y_uno_ajeno(
    client: AsyncClient, session: AsyncSession
) -> None:
    uno = await _account(session, Role.VETERINARIAN, "uno@example.com")
    otro = await _account(session, Role.VETERINARIAN, "otro@example.com")
    creado = await client.post(URL, json=_tramo(), headers=authorization_for(uno))
    slot_id = creado.json()["id"]

    ajeno = await client.delete(f"{URL}/{slot_id}", headers=authorization_for(otro))
    propio = await client.delete(f"{URL}/{slot_id}", headers=authorization_for(uno))

    assert ajeno.status_code == 404
    assert propio.status_code == 204
    resto = await client.get(MINE_URL, headers=authorization_for(uno))
    assert resto.json()["total"] == 0


async def test_el_veterinario_de_emergencia_tambien_publica(
    client: AsyncClient, session: AsyncSession
) -> None:
    vet = await _account(session, Role.EMERGENCY_VETERINARIAN)

    response = await client.post(URL, json=_tramo(), headers=authorization_for(vet))

    assert response.status_code == 201


async def test_el_rango_acota_el_listado(client: AsyncClient, session: AsyncSession) -> None:
    vet = await _account(session, Role.VETERINARIAN)
    cabeceras = authorization_for(vet)
    await client.post(URL, json=_tramo(), headers=cabeceras)
    await client.post(URL, json=_tramo(inicio=BASE + timedelta(days=7)), headers=cabeceras)

    # Se pasa por `params` y no interpolado: un "+00:00" sin codificar viaja
    # como espacio y la fecha deja de parsear.
    semana = await client.get(
        MINE_URL,
        params={"ends_before": (BASE + timedelta(days=1)).isoformat()},
        headers=cabeceras,
    )

    assert semana.status_code == 200
    assert semana.json()["total"] == 1

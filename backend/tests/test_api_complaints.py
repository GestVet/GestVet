"""Pruebas del adaptador HTTP de reclamos.

Recorren la aplicación entera contra una base real, incluida la lectura
hacia la tabla de citas para fijar el veterinario reclamado.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.appointments.adapters.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
)
from gestvet.modules.appointments.domain.entities import Appointment
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import GENERAL_TYPE_ID, authorization_for, build_pet, build_user

URL = "/api/v1/complaints"
HORA = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)

RECLAMO = {"description": "El veterinario no revisó bien a mi mascota."}


class Escenario:
    def __init__(self, cliente, veterinario, cita_id: int) -> None:
        self.cliente = cliente
        self.veterinario = veterinario
        self.cita_id = cita_id


async def montar(session: AsyncSession) -> Escenario:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()

    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=cliente.id or 0))
    appointments = SqlAlchemyAppointmentRepository(session)
    cita = await appointments.add(
        Appointment(
            scheduled_at=HORA,
            duration=timedelta(minutes=30),
            client_id=cliente.id or 0,
            pet_id=mascota.id or 0,
            veterinarian_id=veterinario.id or 0,
            appointment_type_id=GENERAL_TYPE_ID,
        )
    )
    await session.commit()
    return Escenario(cliente, veterinario, cita.id or 0)


def _archivo(nombre: str = "foto.jpg", tipo: str = "image/jpeg") -> dict:
    return {"file": (nombre, b"contenido-de-prueba", tipo)}


async def test_el_cliente_presenta_un_reclamo(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**RECLAMO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == escenario.cliente.id
    assert body["veterinarian_id"] == escenario.veterinario.id
    assert body["appointment_id"] == escenario.cita_id
    assert body["evidence"] == []


async def test_no_se_reclama_una_cita_ajena(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.post(
        URL,
        json={**RECLAMO, "appointment_id": escenario.cita_id},
        headers=authorization_for(otro),
    )

    assert response.status_code == 404


async def test_no_se_reclama_una_cita_inexistente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL, json={**RECLAMO, "appointment_id": 999}, headers=authorization_for(escenario.cliente)
    )

    assert response.status_code == 404


async def test_solo_un_cliente_presenta_reclamos(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**RECLAMO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 403


async def test_el_cliente_ve_su_propio_reclamo(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    await client.post(URL, json={**RECLAMO, "appointment_id": escenario.cita_id}, headers=cabeceras)

    response = await client.get(URL, headers=cabeceras)

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_un_cliente_no_ve_el_reclamo_de_otro(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await client.post(
        URL,
        json={**RECLAMO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.get(URL, headers=authorization_for(otro))

    assert response.status_code == 200
    assert response.json()["total"] == 0


async def test_el_personal_ve_cualquier_reclamo(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    await client.post(
        URL,
        json={**RECLAMO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )
    users = SqlAlchemyUserRepository(session)
    admin = await users.add(build_user("jefa@example.com", role=Role.ADMIN))
    await session.commit()

    response = await client.get(URL, headers=authorization_for(admin))

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_el_cliente_adjunta_evidencia_a_su_reclamo(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    creado = await client.post(
        URL, json={**RECLAMO, "appointment_id": escenario.cita_id}, headers=cabeceras
    )
    complaint_id = creado.json()["id"]

    response = await client.post(
        f"{URL}/{complaint_id}/evidence", files=_archivo(), headers=cabeceras
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "foto.jpg"

    listado = await client.get(URL, headers=cabeceras)
    assert len(listado.json()["items"][0]["evidence"]) == 1


async def test_no_se_adjunta_evidencia_al_reclamo_de_otro(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creado = await client.post(
        URL,
        json={**RECLAMO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )
    complaint_id = creado.json()["id"]
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.post(
        f"{URL}/{complaint_id}/evidence", files=_archivo(), headers=authorization_for(otro)
    )

    assert response.status_code == 404


async def test_un_tipo_de_evidencia_no_permitido_se_rechaza(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    creado = await client.post(
        URL, json={**RECLAMO, "appointment_id": escenario.cita_id}, headers=cabeceras
    )
    complaint_id = creado.json()["id"]

    response = await client.post(
        f"{URL}/{complaint_id}/evidence",
        files=_archivo("virus.exe", "application/x-msdownload"),
        headers=cabeceras,
    )

    assert response.status_code == 422


async def test_sin_credencial_no_se_llega_a_ninguna_parte(client: AsyncClient) -> None:
    assert (await client.post(URL, json={**RECLAMO, "appointment_id": 1})).status_code == 401
    assert (await client.get(URL)).status_code == 401
    assert (await client.post(f"{URL}/1/evidence", files=_archivo())).status_code == 401


async def test_el_listado_dice_quien_reclama_de_que_mascota_y_en_que_cita(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await client.post(
        URL,
        json={**RECLAMO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )

    response = await client.get(URL, headers=authorization_for(escenario.cliente))

    reclamo = response.json()["items"][0]
    assert reclamo["client_name"] == "Ana Quispe"
    assert reclamo["veterinarian_name"] == "Ana Quispe"
    assert reclamo["pet_name"] == "Rocco"
    assert reclamo["appointment_type"] == "Consulta general"
    assert reclamo["appointment_at"].startswith("2026-09-14T10:00")

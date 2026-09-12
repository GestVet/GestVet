"""Pruebas del adaptador HTTP de internaciones.

Recorren la aplicación entera contra una base real, incluida la lectura
hacia las tablas de citas y mascotas para resolver la mascota internada y
aplicar el recorte por dueño.
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

URL = "/api/v1/hospitalizations"
HORA = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)

INTERNACION = {"reason": "Cirugía de emergencia, queda en observación."}


class Escenario:
    def __init__(self, cliente, veterinario, pet_id: int, cita_id: int) -> None:
        self.cliente = cliente
        self.veterinario = veterinario
        self.pet_id = pet_id
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
    return Escenario(cliente, veterinario, mascota.id or 0, cita.id or 0)


async def _abrir(client: AsyncClient, escenario: Escenario) -> str:
    creada = await client.post(
        URL,
        json={**INTERNACION, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.veterinario),
    )
    return creada.json()["id"]


async def test_el_veterinario_abre_una_internacion(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**INTERNACION, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["pet_id"] == escenario.pet_id
    assert body["opened_by"] == escenario.veterinario.id
    assert body["status"] == "open"
    assert body["notes"] == []


async def test_un_cliente_no_puede_abrir_una_internacion(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**INTERNACION, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_no_se_abre_una_internacion_de_una_cita_inexistente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**INTERNACION, "appointment_id": 999},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 404


async def test_el_veterinario_agrega_una_nota(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    hospitalization_id = await _abrir(client, escenario)

    response = await client.post(
        f"{URL}/{hospitalization_id}/notes",
        json={"note": "Comió bien, signos vitales estables."},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 201
    assert response.json()["note"] == "Comió bien, signos vitales estables."


async def test_no_se_agrega_una_nota_a_una_internacion_dada_de_alta(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    hospitalization_id = await _abrir(client, escenario)
    cabeceras = authorization_for(escenario.veterinario)
    await client.post(f"{URL}/{hospitalization_id}/discharge", json={}, headers=cabeceras)

    response = await client.post(
        f"{URL}/{hospitalization_id}/notes", json={"note": "Tarde."}, headers=cabeceras
    )

    assert response.status_code == 409


async def test_el_veterinario_da_de_alta(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    hospitalization_id = await _abrir(client, escenario)

    response = await client.post(
        f"{URL}/{hospitalization_id}/discharge",
        json={"discharge_notes": "Se recuperó bien, vuelve a casa."},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "discharged"
    assert body["discharge_notes"] == "Se recuperó bien, vuelve a casa."
    assert body["discharged_at"] is not None


async def test_no_se_da_de_alta_dos_veces(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    hospitalization_id = await _abrir(client, escenario)
    cabeceras = authorization_for(escenario.veterinario)
    await client.post(f"{URL}/{hospitalization_id}/discharge", json={}, headers=cabeceras)

    response = await client.post(
        f"{URL}/{hospitalization_id}/discharge", json={}, headers=cabeceras
    )

    assert response.status_code == 409


async def test_el_cliente_ve_la_internacion_de_su_mascota(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await _abrir(client, escenario)

    response = await client.get(
        URL, params={"pet_id": escenario.pet_id}, headers=authorization_for(escenario.cliente)
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_un_cliente_no_ve_la_internacion_de_la_mascota_de_otro(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await _abrir(client, escenario)
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.get(
        URL, params={"pet_id": escenario.pet_id}, headers=authorization_for(otro)
    )

    assert response.status_code == 404


async def test_el_personal_ve_la_internacion_de_cualquier_mascota(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await _abrir(client, escenario)
    users = SqlAlchemyUserRepository(session)
    admin = await users.add(build_user("jefa@example.com", role=Role.ADMIN))
    await session.commit()

    response = await client.get(
        URL, params={"pet_id": escenario.pet_id}, headers=authorization_for(admin)
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_sin_credencial_no_se_llega_a_ninguna_parte(client: AsyncClient) -> None:
    assert (await client.post(URL, json={**INTERNACION, "appointment_id": 1})).status_code == 401
    assert (await client.get(URL, params={"pet_id": 1})).status_code == 401
    assert (await client.post(f"{URL}/1/notes", json={"note": "x"})).status_code == 401
    assert (await client.post(f"{URL}/1/discharge", json={})).status_code == 401

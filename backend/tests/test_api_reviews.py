"""Pruebas del adaptador HTTP de reseñas.

Recorren la aplicación entera contra una base real, incluida la lectura
hacia la tabla de citas para verificar la elegibilidad.
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

URL = "/api/v1/reviews"
HORA = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)

RESENA = {"rating": 5, "comment": "Excelente atención, muy atento con mi mascota."}


class Escenario:
    def __init__(self, cliente, veterinario) -> None:
        self.cliente = cliente
        self.veterinario = veterinario


async def montar(session: AsyncSession, *, atendido: bool = True) -> Escenario:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()

    if atendido:
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
        cita.confirm(veterinario.id or 0)
        cita.complete(veterinario.id or 0)
        await appointments.save(cita)

    await session.commit()
    return Escenario(cliente, veterinario)


async def test_el_cliente_deja_una_resena(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**RESENA, "veterinarian_id": escenario.veterinario.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["rating"] == 5
    assert body["client_id"] == escenario.cliente.id
    assert body["veterinarian_id"] == escenario.veterinario.id


async def test_no_se_puede_resenar_sin_haber_sido_atendido(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session, atendido=False)

    response = await client.post(
        URL,
        json={**RESENA, "veterinarian_id": escenario.veterinario.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_solo_un_cliente_puede_resenar(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**RESENA, "veterinarian_id": escenario.veterinario.id},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 403


async def test_una_calificacion_fuera_de_rango_se_rechaza(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**RESENA, "veterinarian_id": escenario.veterinario.id, "rating": 6},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 422


async def test_un_comentario_con_groserias_se_rechaza(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={
            "veterinarian_id": escenario.veterinario.id,
            "rating": 1,
            "comment": "Que atencion tan de mierda",
        },
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 422


async def test_volver_a_resenar_actualiza_la_reseña_existente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    primera = await client.post(
        URL, json={**RESENA, "veterinarian_id": escenario.veterinario.id}, headers=cabeceras
    )

    segunda = await client.post(
        URL,
        json={
            "veterinarian_id": escenario.veterinario.id,
            "rating": 2,
            "comment": "Lo pienso de nuevo, no fue tan buena la atención",
        },
        headers=cabeceras,
    )

    assert segunda.status_code == 201
    assert segunda.json()["id"] == primera.json()["id"]
    assert segunda.json()["rating"] == 2


async def test_el_listado_trae_el_promedio_y_las_resenas(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    cabeceras_cliente = authorization_for(escenario.cliente)
    await client.post(
        URL, json={**RESENA, "veterinarian_id": escenario.veterinario.id}, headers=cabeceras_cliente
    )

    response = await client.get(
        URL,
        params={"veterinarian_id": escenario.veterinario.id},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["count"] == 1
    assert body["summary"]["average"] == "5.0"
    assert body["total"] == 1
    assert body["items"][0]["rating"] == 5


async def test_un_veterinario_sin_resenas_devuelve_promedio_vacio(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session, atendido=False)

    response = await client.get(
        URL,
        params={"veterinarian_id": escenario.veterinario.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["average"] is None
    assert body["summary"]["count"] == 0


async def test_sin_credencial_no_se_llega_a_ninguna_parte(client: AsyncClient) -> None:
    assert (await client.post(URL, json={**RESENA, "veterinarian_id": 1})).status_code == 401
    assert (await client.get(URL, params={"veterinarian_id": 1})).status_code == 401


async def test_el_promedio_aparece_al_elegir_veterinario_para_reservar(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Es el mismo listado que usa la reserva de citas: HU06."""
    escenario = await montar(session)
    await client.post(
        URL,
        json={**RESENA, "veterinarian_id": escenario.veterinario.id},
        headers=authorization_for(escenario.cliente),
    )

    response = await client.get(
        "/api/v1/veterinarians", headers=authorization_for(escenario.cliente)
    )

    assert response.status_code == 200
    vet = next(item for item in response.json()["items"] if item["id"] == escenario.veterinario.id)
    assert vet["average_rating"] == "5.0"
    assert vet["review_count"] == 1

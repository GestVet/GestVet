"""Pruebas de la bitacora de movimientos.

Cubren las dos mitades: que cada caso de uso deje su asiento, y que la
administracion pueda leerlos con el nombre y el rol de quien los hizo.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.clinic_time import clinic_date, clinic_midnight
from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.availability.adapters.persistence.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityRepository,
)
from gestvet.modules.availability.domain.entities import AvailabilitySlot
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import (
    GENERAL_TYPE_ID,
    VALID_PASSWORD,
    authorization_for,
    build_pet,
    build_user,
)

ACTIVITY_URL = "/api/v1/activity"
JORNADA = datetime(2026, 9, 14, 9, 0, tzinfo=UTC)


async def _cuenta(session: AsyncSession, role: Role, email: str | None = None):
    users = SqlAlchemyUserRepository(session)
    cuenta = await users.add(build_user(email or f"{role.value}@example.com", role=role))
    await session.commit()
    return cuenta


async def _asientos(client: AsyncClient, jefa, **params: object) -> dict:
    response = await client.get(ACTIVITY_URL, params=params, headers=authorization_for(jefa))
    assert response.status_code == 200
    return response.json()


async def test_el_acceso_deja_asiento(client: AsyncClient, session: AsyncSession) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    await _cuenta(session, Role.CLIENT, "ana@example.com")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": VALID_PASSWORD},
    )

    cuerpo = await _asientos(client, jefa)

    assert cuerpo["total"] == 1
    asiento = cuerpo["items"][0]
    assert asiento["kind"] == "signed_in"
    assert asiento["kind_label"] == "Inició sesión"
    assert asiento["user_name"] == "Ana Quispe"
    assert asiento["user_role"] == Role.CLIENT.value


async def test_el_autorregistro_deja_asiento(client: AsyncClient, session: AsyncSession) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nueva@example.com",
            "password": VALID_PASSWORD,
            "first_name": "Nueva",
            "last_name": "Cuenta",
            "document_id": "87654321",
            "accepts_identity_check": True,
            "accepts_terms": True,
        },
    )

    cuerpo = await _asientos(client, jefa)

    assert [item["kind"] for item in cuerpo["items"]] == ["client_registered"]


async def test_registrar_una_mascota_deja_asiento_con_su_nombre(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    ana = await _cuenta(session, Role.CLIENT, "ana@example.com")

    await client.post(
        "/api/v1/pets",
        json={
            "name": "Rocco",
            "species": "Perro",
            "breed": "Mestizo",
            "birth_date": "2020-05-17",
        },
        headers=authorization_for(ana),
    )

    cuerpo = await _asientos(client, jefa)
    asiento = cuerpo["items"][0]
    assert asiento["kind"] == "pet_registered"
    assert asiento["detail"] == "Rocco"


async def test_asignar_y_quitar_un_turno_dejan_asiento(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    vet = await _cuenta(session, Role.VETERINARIAN, "vet@example.com")
    cabeceras = authorization_for(jefa)
    dia = clinic_date(datetime.now(UTC)) + timedelta(days=2)
    inicio = clinic_midnight(dia) + timedelta(hours=9)

    creado = await client.post(
        "/api/v1/availability/shifts",
        json={
            "veterinarian_id": vet.id,
            "starts_at": inicio.isoformat(),
            "ends_at": (inicio + timedelta(hours=8)).isoformat(),
        },
        headers=cabeceras,
    )
    await client.delete(f"/api/v1/availability/shifts/{creado.json()['id']}", headers=cabeceras)

    cuerpo = await _asientos(client, jefa)

    assert [item["kind"] for item in cuerpo["items"]] == ["shift_removed", "shift_assigned"]
    # El asiento de la baja conserva de qué turno se trataba, en hora de la clínica.
    assert f"{dia:%d/%m/%Y} 09:00" in cuerpo["items"][0]["detail"]


async def test_el_ciclo_de_una_cita_deja_sus_asientos(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    ana = await _cuenta(session, Role.CLIENT, "ana@example.com")
    vet = await _cuenta(session, Role.VETERINARIAN, "vet@example.com")

    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=ana.id or 0))
    slots = SqlAlchemyAvailabilityRepository(session)
    await slots.add(
        AvailabilitySlot(
            veterinarian_id=vet.id or 0,
            starts_at=JORNADA,
            ends_at=JORNADA + timedelta(hours=8),
        )
    )
    await session.commit()

    creada = await client.post(
        "/api/v1/appointments",
        json={
            "pet_id": mascota.id,
            "veterinarian_id": vet.id,
            "appointment_type_id": GENERAL_TYPE_ID,
            "scheduled_at": (JORNADA + timedelta(hours=1)).isoformat(),
        },
        headers=authorization_for(ana),
    )
    cita_id = creada.json()["id"]
    await client.post(f"/api/v1/appointments/{cita_id}/confirm", headers=authorization_for(vet))
    await client.post(
        f"/api/v1/appointments/{cita_id}/cancel",
        json={"reason": "Se enfermo el veterinario"},
        headers=authorization_for(vet),
    )

    cuerpo = await _asientos(client, jefa)

    assert [item["kind"] for item in cuerpo["items"]] == [
        "appointment_cancelled",
        "appointment_confirmed",
        "appointment_booked",
    ]
    assert cuerpo["items"][0]["detail"] == "Se enfermo el veterinario"


async def test_las_acciones_de_la_administracion_tambien_quedan(
    client: AsyncClient, session: AsyncSession
) -> None:
    """El original las escondia con un `id_rol != 1` fijo en la consulta."""
    jefa = await _cuenta(session, Role.ADMIN)

    await client.post(
        "/api/v1/staff",
        json={
            "email": "carla@example.com",
            "password": VALID_PASSWORD,
            "first_name": "Carla",
            "last_name": "Blanco",
            "role": Role.VETERINARIAN.value,
        },
        headers=authorization_for(jefa),
    )

    cuerpo = await _asientos(client, jefa)

    asiento = cuerpo["items"][0]
    assert asiento["kind"] == "staff_registered"
    assert asiento["user_role"] == Role.ADMIN.value
    assert asiento["detail"] == "carla@example.com"


async def test_el_filtro_por_rol_acota_la_bitacora(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    ana = await _cuenta(session, Role.CLIENT, "ana@example.com")
    vet = await _cuenta(session, Role.VETERINARIAN, "vet@example.com")
    await client.patch(
        "/api/v1/auth/me",
        json={"first_name": "Ana", "last_name": "Quispe", "phone": ""},
        headers=authorization_for(ana),
    )
    await client.post(
        "/api/v1/availability/change-requests",
        json={"message": "Necesito cambiar el turno del lunes"},
        headers=authorization_for(vet),
    )

    de_clientes = await _asientos(client, jefa, role=Role.CLIENT.value)
    de_veterinarios = await _asientos(client, jefa, role=Role.VETERINARIAN.value)

    assert [item["kind"] for item in de_clientes["items"]] == ["profile_updated"]
    assert [item["kind"] for item in de_veterinarios["items"]] == ["shift_change_requested"]


async def test_el_filtro_por_accion_acota_la_bitacora(
    client: AsyncClient, session: AsyncSession
) -> None:
    jefa = await _cuenta(session, Role.ADMIN)
    ana = await _cuenta(session, Role.CLIENT, "ana@example.com")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": VALID_PASSWORD},
    )
    await client.patch(
        "/api/v1/auth/me",
        json={"first_name": "Ana", "last_name": "Quispe", "phone": ""},
        headers=authorization_for(ana),
    )

    solo_accesos = await _asientos(client, jefa, kind="signed_in")

    assert [item["kind"] for item in solo_accesos["items"]] == ["signed_in"]


@pytest.mark.parametrize("rol", [Role.CLIENT, Role.VETERINARIAN])
async def test_la_bitacora_es_solo_para_la_administracion(
    client: AsyncClient, session: AsyncSession, rol: Role
) -> None:
    cuenta = await _cuenta(session, rol, f"{rol.value}@example.com")

    response = await client.get(ACTIVITY_URL, headers=authorization_for(cuenta))

    assert response.status_code == 403


async def test_la_bitacora_no_se_lee_sin_credencial(client: AsyncClient) -> None:
    assert (await client.get(ACTIVITY_URL)).status_code == 401


async def test_un_acceso_fallido_no_deja_asiento(
    client: AsyncClient, session: AsyncSession
) -> None:
    """La bitacora guarda acciones completadas, no intentos.

    Un intento fallido no deja rastro por dos motivos que se suman: el asiento
    se escribe recien despues de que la operacion sale bien, y ademas viaja en
    la misma transaccion que la peticion, asi que un error lo deshace igual.
    """
    jefa = await _cuenta(session, Role.ADMIN)
    await _cuenta(session, Role.CLIENT, "ana@example.com")

    fallido = await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "equivocada-larga"},
    )

    assert fallido.status_code == 401
    assert (await _asientos(client, jefa))["total"] == 0

"""Pruebas de la agenda: turnos que asigna la clínica y pedidos de cambio.

Las fechas se arman relativas al momento en que corre la prueba: la agenda no
acepta turnos en días que ya pasaron.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.clinic_time import clinic_date, clinic_midnight
from gestvet.core.identity import Role
from gestvet.core.realtime import SCHEDULE_TOPIC
from gestvet.core.realtime_broker import LocalBroker
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.appointments.adapters.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
)
from gestvet.modules.appointments.domain.entities import Appointment
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import GENERAL_TYPE_ID, authorization_for, build_pet, build_user

URL = "/api/v1/availability"
MINE_URL = f"{URL}/mine"
ROSTER_URL = f"{URL}/roster"
SHIFTS_URL = f"{URL}/shifts"
PLAN_URL = f"{URL}/weekly-plan"
REQUESTS_URL = f"{URL}/change-requests"


def dia(dias: int, horas: float = 0) -> datetime:
    """Una hora de la clínica, contando días desde hoy."""
    hoy = clinic_date(datetime.now(UTC))
    return clinic_midnight(hoy + timedelta(days=dias)) + timedelta(hours=horas)


def turno(
    veterinario: User, inicio: datetime, horas: float = 4, kind: str = "regular"
) -> dict[str, object]:
    return {
        "veterinarian_id": veterinario.id,
        "starts_at": inicio.isoformat(),
        "ends_at": (inicio + timedelta(hours=horas)).isoformat(),
        "kind": kind,
    }


async def _account(session: AsyncSession, role: Role, email: str | None = None) -> User:
    users = SqlAlchemyUserRepository(session)
    account = await users.add(build_user(email or f"{role.value}@example.com", role=role))
    await session.commit()
    return account


async def _clinica(session: AsyncSession) -> tuple[User, User]:
    admin = await _account(session, Role.ADMIN)
    vet = await _account(session, Role.VETERINARIAN)
    return admin, vet


async def test_la_administracion_asigna_un_turno(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)

    response = await client.post(
        SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=authorization_for(admin)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["veterinarian_id"] == vet.id
    assert body["kind"] == "regular"
    assert body["assigned_by"] == admin.id
    assert body["duration_minutes"] == 240


async def test_un_veterinario_no_se_asigna_turnos(
    client: AsyncClient, session: AsyncSession
) -> None:
    _, vet = await _clinica(session)

    response = await client.post(
        SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=authorization_for(vet)
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "inicio",
    [
        pytest.param(lambda: dia(-1, 9), id="ayer"),
        pytest.param(lambda: dia(400, 9), id="dentro-de-mas-de-un-ano"),
        pytest.param(lambda: datetime(3000, 1, 1, 14, tzinfo=UTC), id="año-3000"),
    ],
)
async def test_un_turno_fuera_de_fecha_se_rechaza(
    client: AsyncClient, session: AsyncSession, inicio
) -> None:
    admin, vet = await _clinica(session)

    response = await client.post(
        SHIFTS_URL, json=turno(vet, inicio()), headers=authorization_for(admin)
    )

    assert response.status_code == 422


async def test_un_turno_superpuesto_se_rechaza_y_uno_contiguo_no(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    cabeceras = authorization_for(admin)
    await client.post(SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=cabeceras)

    pisado = await client.post(SHIFTS_URL, json=turno(vet, dia(2, 11)), headers=cabeceras)
    contiguo = await client.post(SHIFTS_URL, json=turno(vet, dia(2, 13)), headers=cabeceras)

    assert pisado.status_code == 409
    assert contiguo.status_code == 201


async def test_la_noche_se_cubre_con_una_guardia_no_con_un_turno_de_atencion(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    cabeceras = authorization_for(admin)

    atencion = await client.post(
        SHIFTS_URL, json=turno(vet, dia(2, 20), horas=12), headers=cabeceras
    )
    guardia = await client.post(
        SHIFTS_URL, json=turno(vet, dia(2, 20), horas=12, kind="on_call"), headers=cabeceras
    )

    assert atencion.status_code == 422
    assert guardia.status_code == 201
    assert guardia.json()["kind"] == "on_call"


async def test_solo_se_asignan_turnos_a_veterinarios_activos(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, _ = await _clinica(session)
    cliente = await _account(session, Role.CLIENT, "ana@example.com")
    cabeceras = authorization_for(admin)

    a_un_cliente = await client.post(SHIFTS_URL, json=turno(cliente, dia(2, 9)), headers=cabeceras)
    inexistente = await client.post(
        SHIFTS_URL,
        json={**turno(cliente, dia(2, 9)), "veterinarian_id": 9999},
        headers=cabeceras,
    )

    assert a_un_cliente.status_code == 404
    assert inexistente.status_code == 404


async def test_una_hora_sin_zona_horaria_se_rechaza(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    cuerpo = turno(vet, dia(2, 9))
    cuerpo["starts_at"] = str(cuerpo["starts_at"])[:19]

    response = await client.post(SHIFTS_URL, json=cuerpo, headers=authorization_for(admin))

    assert response.status_code == 422


async def test_el_veterinario_ve_solo_sus_turnos(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    otro = await _account(session, Role.VETERINARIAN, "otro@example.com")
    await client.post(SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=authorization_for(admin))

    propios = await client.get(MINE_URL, headers=authorization_for(vet))
    ajenos = await client.get(MINE_URL, headers=authorization_for(otro))

    assert propios.json()["total"] == 1
    assert ajenos.json()["total"] == 0


async def test_un_cliente_consulta_la_agenda_de_un_veterinario(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Necesita verla para poder reservar."""
    admin, vet = await _clinica(session)
    cliente = await _account(session, Role.CLIENT, "ana@example.com")
    await client.post(SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=authorization_for(admin))

    response = await client.get(
        URL, params={"veterinarian_id": vet.id}, headers=authorization_for(cliente)
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_la_agenda_no_se_consulta_sin_credencial(client: AsyncClient) -> None:
    assert (await client.get(f"{URL}?veterinarian_id=1")).status_code == 401


async def test_quitar_un_turno(client: AsyncClient, session: AsyncSession) -> None:
    admin, vet = await _clinica(session)
    cabeceras = authorization_for(admin)
    creado = await client.post(SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=cabeceras)
    url = f"{SHIFTS_URL}/{creado.json()['id']}"

    quitado = await client.delete(url, headers=cabeceras)
    otra_vez = await client.delete(url, headers=cabeceras)

    assert quitado.status_code == 204
    assert otra_vez.status_code == 404


async def test_no_se_quita_un_turno_con_citas_reservadas(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    cliente = await _account(session, Role.CLIENT, "ana@example.com")
    cabeceras = authorization_for(admin)
    creado = await client.post(SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=cabeceras)
    mascota = await SqlAlchemyPetRepository(session).add(build_pet(owner_id=cliente.id or 0))
    await SqlAlchemyAppointmentRepository(session).add(
        Appointment(
            scheduled_at=dia(2, 10),
            duration=timedelta(minutes=30),
            client_id=cliente.id or 0,
            pet_id=mascota.id or 0,
            veterinarian_id=vet.id or 0,
            appointment_type_id=GENERAL_TYPE_ID,
        )
    )
    await session.commit()

    response = await client.delete(f"{SHIFTS_URL}/{creado.json()['id']}", headers=cabeceras)

    assert response.status_code == 409


async def test_el_horario_semanal_crea_los_turnos_de_cada_semana(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    manana = clinic_date(datetime.now(UTC)) + timedelta(days=1)
    plan = {
        "veterinarian_id": vet.id,
        "first_day": manana.isoformat(),
        "weeks": 2,
        "shifts": [
            {"weekday": manana.weekday(), "starts": "09:00", "ends": "13:00"},
            {
                "weekday": (manana.weekday() + 2) % 7,
                "starts": "20:00",
                "ends": "08:00",
                "kind": "on_call",
            },
        ],
    }

    response = await client.post(PLAN_URL, json=plan, headers=authorization_for(admin))

    assert response.status_code == 201
    assert response.json()["total"] == 4
    kinds = sorted(item["kind"] for item in response.json()["items"])
    assert kinds == ["on_call", "on_call", "regular", "regular"]


async def test_el_horario_semanal_es_todo_o_nada(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    cabeceras = authorization_for(admin)
    await client.post(SHIFTS_URL, json=turno(vet, dia(8, 10), horas=1), headers=cabeceras)
    manana = clinic_date(datetime.now(UTC)) + timedelta(days=1)
    plan = {
        "veterinarian_id": vet.id,
        "first_day": manana.isoformat(),
        "weeks": 2,
        "shifts": [{"weekday": manana.weekday(), "starts": "09:00", "ends": "13:00"}],
    }

    response = await client.post(PLAN_URL, json=plan, headers=cabeceras)

    assert response.status_code == 409
    restantes = await client.get(MINE_URL, headers=authorization_for(vet))
    assert restantes.json()["total"] == 1


async def test_el_plantel_lista_los_turnos_de_todo_el_equipo(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    otro = await _account(session, Role.VETERINARIAN, "otro@example.com")
    cabeceras = authorization_for(admin)
    await client.post(SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=cabeceras)
    await client.post(SHIFTS_URL, json=turno(otro, dia(3, 9)), headers=cabeceras)
    semana = {"starts_after": dia(0).isoformat(), "ends_before": dia(7).isoformat()}

    plantel = await client.get(ROSTER_URL, params=semana, headers=cabeceras)
    muy_largo = await client.get(
        ROSTER_URL,
        params={"starts_after": dia(0).isoformat(), "ends_before": dia(60).isoformat()},
        headers=cabeceras,
    )
    de_un_veterinario = await client.get(ROSTER_URL, params=semana, headers=authorization_for(vet))

    assert plantel.json()["total"] == 2
    assert muy_largo.status_code == 422
    assert de_un_veterinario.status_code == 403


async def test_el_veterinario_pide_un_cambio_y_la_administracion_responde(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    creado = await client.post(
        SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=authorization_for(admin)
    )

    pedido = await client.post(
        REQUESTS_URL,
        json={"message": "Tengo control médico ese día", "slot_id": creado.json()["id"]},
        headers=authorization_for(vet),
    )
    assert pedido.status_code == 201
    assert pedido.json()["status"] == "pending"

    pendientes = await client.get(
        REQUESTS_URL, params={"status": "pending"}, headers=authorization_for(admin)
    )
    assert [item["id"] for item in pendientes.json()["items"]] == [pedido.json()["id"]]

    resolver = f"{REQUESTS_URL}/{pedido.json()['id']}/resolve"
    respuesta = await client.post(
        resolver,
        json={"accepted": True, "response": "Lo cubre Pedro"},
        headers=authorization_for(admin),
    )
    otra_vez = await client.post(
        resolver, json={"accepted": False}, headers=authorization_for(admin)
    )
    del_veterinario = await client.post(
        resolver, json={"accepted": True}, headers=authorization_for(vet)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "accepted"
    assert otra_vez.status_code == 409
    assert del_veterinario.status_code == 403
    mios = await client.get(f"{REQUESTS_URL}/mine", headers=authorization_for(vet))
    assert mios.json()["items"][0]["response"] == "Lo cubre Pedro"


async def test_no_se_pide_cambio_sobre_el_turno_de_otro(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, vet = await _clinica(session)
    otro = await _account(session, Role.VETERINARIAN, "otro@example.com")
    creado = await client.post(
        SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=authorization_for(admin)
    )

    response = await client.post(
        REQUESTS_URL,
        json={"message": "Quiero ese turno", "slot_id": creado.json()["id"]},
        headers=authorization_for(otro),
    )

    assert response.status_code == 404


async def test_asignar_un_turno_avisa_al_veterinario(
    client: AsyncClient, session: AsyncSession, broker: LocalBroker
) -> None:
    admin, vet = await _clinica(session)

    async with broker.subscribe() as queue:
        await client.post(SHIFTS_URL, json=turno(vet, dia(2, 9)), headers=authorization_for(admin))
        event = queue.get_nowait()

    assert event.topic == SCHEDULE_TOPIC
    assert event.user_ids == frozenset({vet.id})
    assert Role.ADMIN in event.roles

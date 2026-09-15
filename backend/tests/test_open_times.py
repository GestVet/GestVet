"""Horas libres para reservar.

Las fechas se arman relativas al momento en que corre la prueba: con una fecha
fija, el día que esa fecha pase las horas dejarían de ofrecerse y la prueba
fallaría sin que el código cambiara.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

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
from gestvet.modules.appointments.use_cases.list_open_times import clinic_date, clinic_midnight
from gestvet.modules.availability.adapters.persistence.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityRepository,
)
from gestvet.modules.availability.domain.entities import AvailabilitySlot, ShiftKind
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import (
    EMERGENCY_TYPE_ID,
    GENERAL_TYPE_ID,
    authorization_for,
    build_pet,
    build_user,
)

URL = "/api/v1/appointments/open-times"


def pasado_manana_a_las(horas: float) -> datetime:
    """Una hora de la clínica dentro de dos días."""
    dia = clinic_date(datetime.now(UTC)) + timedelta(days=2)
    return clinic_midnight(dia) + timedelta(hours=horas)


async def montar(
    session: AsyncSession,
    desde: datetime,
    hasta: datetime,
    kind: ShiftKind = ShiftKind.REGULAR,
) -> tuple[object, object, object]:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()
    mascota = await SqlAlchemyPetRepository(session).add(build_pet(owner_id=cliente.id or 0))
    await SqlAlchemyAvailabilityRepository(session).add(
        AvailabilitySlot(
            veterinarian_id=veterinario.id or 0, starts_at=desde, ends_at=hasta, kind=kind
        )
    )
    await session.commit()
    return cliente, mascota, veterinario


def estados(oferta: dict[str, Any]) -> dict[datetime, str]:
    return {datetime.fromisoformat(slot["time"]): slot["status"] for slot in oferta["slots"]}


def libres(oferta: dict[str, Any]) -> list[datetime]:
    return [hora for hora, estado in estados(oferta).items() if estado == "available"]


async def test_ofrece_cada_cuarto_de_hora_en_que_la_cita_cabe(
    client: AsyncClient, session: AsyncSession
) -> None:
    inicio = pasado_manana_a_las(9)
    cliente, _, veterinario = await montar(session, inicio, inicio + timedelta(hours=1))

    response = await client.get(
        URL, params={"appointment_type_id": GENERAL_TYPE_ID}, headers=authorization_for(cliente)
    )

    assert response.status_code == 200
    dias = response.json()["days"]
    assert [dia["day"] for dia in dias] == [clinic_date(inicio).isoformat()]
    oferta = dias[0]["veterinarians"][0]
    assert oferta["veterinarian_id"] == veterinario.id
    # Consulta general de 30 minutos en un tramo de 9:00 a 10:00: la última
    # hora posible es 9:30, que termina justo al cierre.
    assert libres(oferta) == [
        inicio,
        inicio + timedelta(minutes=15),
        inicio + timedelta(minutes=30),
    ]


async def test_las_horas_que_no_alcanzan_antes_del_cierre_salen_marcadas(
    client: AsyncClient, session: AsyncSession
) -> None:
    inicio = pasado_manana_a_las(9)
    cliente, _, _ = await montar(session, inicio, inicio + timedelta(hours=1))

    response = await client.get(
        URL, params={"appointment_type_id": GENERAL_TYPE_ID}, headers=authorization_for(cliente)
    )

    oferta = response.json()["days"][0]["veterinarians"][0]
    assert estados(oferta)[inicio + timedelta(minutes=45)] == "too_short"
    turnos = [
        (datetime.fromisoformat(w["starts_at"]), datetime.fromisoformat(w["ends_at"]))
        for w in oferta["windows"]
    ]
    assert turnos == [(inicio, inicio + timedelta(hours=1))]


async def test_una_cita_existente_bloquea_su_hora_y_el_margen(
    client: AsyncClient, session: AsyncSession
) -> None:
    inicio = pasado_manana_a_las(9)
    cliente, mascota, veterinario = await montar(session, inicio, inicio + timedelta(hours=2))
    await SqlAlchemyAppointmentRepository(session).add(
        Appointment(
            scheduled_at=inicio + timedelta(minutes=30),
            duration=timedelta(minutes=30),
            client_id=cliente.id,
            pet_id=mascota.id,
            veterinarian_id=veterinario.id,
            appointment_type_id=GENERAL_TYPE_ID,
        )
    )
    await session.commit()

    response = await client.get(
        URL, params={"appointment_type_id": GENERAL_TYPE_ID}, headers=authorization_for(cliente)
    )

    oferta = response.json()["days"][0]["veterinarians"][0]
    # La cita ocupa de 9:30 a 10:00 y el margen de 10 minutos corre a los dos
    # lados: la primera hora libre es 10:15 y la última que cabe, 10:30.
    assert libres(oferta) == [inicio + timedelta(minutes=75), inicio + timedelta(minutes=90)]
    # Las horas que pisa la cita no desaparecen: salen ocupadas.
    assert estados(oferta)[inicio + timedelta(minutes=30)] == "taken"


async def test_no_ofrece_horas_que_ya_pasaron(client: AsyncClient, session: AsyncSession) -> None:
    ahora = datetime.now(UTC)
    cliente, _, _ = await montar(session, ahora - timedelta(hours=2), ahora + timedelta(hours=2))

    response = await client.get(
        URL, params={"appointment_type_id": GENERAL_TYPE_ID}, headers=authorization_for(cliente)
    )

    todas = {
        hora: estado
        for dia in response.json()["days"]
        for oferta in dia["veterinarians"]
        for hora, estado in estados(oferta).items()
    }
    assert any(estado == "available" for estado in todas.values())
    assert all(hora >= ahora for hora, estado in todas.items() if estado == "available")
    assert all(estado == "past" for hora, estado in todas.items() if hora < ahora)


async def test_una_guardia_no_se_ofrece_para_citas_normales(
    client: AsyncClient, session: AsyncSession
) -> None:
    inicio = pasado_manana_a_las(9)
    cliente, _, _ = await montar(
        session, inicio, inicio + timedelta(hours=2), kind=ShiftKind.ON_CALL
    )

    response = await client.get(
        URL, params={"appointment_type_id": GENERAL_TYPE_ID}, headers=authorization_for(cliente)
    )

    assert response.json()["days"] == []


async def test_una_emergencia_no_tiene_horas_para_reservar(
    client: AsyncClient, session: AsyncSession
) -> None:
    inicio = pasado_manana_a_las(9)
    cliente, _, _ = await montar(session, inicio, inicio + timedelta(hours=2))

    emergencia = await client.get(
        URL, params={"appointment_type_id": EMERGENCY_TYPE_ID}, headers=authorization_for(cliente)
    )
    inexistente = await client.get(
        URL, params={"appointment_type_id": 999}, headers=authorization_for(cliente)
    )

    assert emergencia.status_code == 422
    assert inexistente.status_code == 404


async def test_exige_credencial(client: AsyncClient) -> None:
    response = await client.get(URL, params={"appointment_type_id": GENERAL_TYPE_ID})

    assert response.status_code == 401

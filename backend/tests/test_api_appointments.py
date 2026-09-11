"""Pruebas del adaptador HTTP de citas.

Recorren la aplicacion entera contra una base real, incluidas las dos lecturas
hacia tablas de otros modulos: la pertenencia de la mascota y la agenda
publicada del veterinario.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.availability.adapters.persistence.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityRepository,
)
from gestvet.availability.domain.entities import AvailabilitySlot
from gestvet.core.identity import Role
from gestvet.pets.adapters.persistence.sqlalchemy_pet_repository import SqlAlchemyPetRepository
from tests.conftest import (
    EMERGENCY_TYPE_ID,
    GENERAL_TYPE_ID,
    SURGERY_TYPE_ID,
    authorization_for,
    build_pet,
    build_user,
)

URL = "/api/v1/appointments"
JORNADA = datetime(2026, 9, 14, 9, 0, tzinfo=UTC)
HORA = JORNADA + timedelta(hours=1)


class Escenario:
    """Una clinica minima: un cliente con mascota y un veterinario con agenda."""

    def __init__(self, cliente, mascota, veterinario) -> None:
        self.cliente = cliente
        self.mascota = mascota
        self.veterinario = veterinario

    def reserva(self, **extra: object) -> dict[str, object]:
        cuerpo: dict[str, object] = {
            "pet_id": self.mascota.id,
            "veterinarian_id": self.veterinario.id,
            "appointment_type_id": GENERAL_TYPE_ID,
            "scheduled_at": HORA.isoformat(),
        }
        cuerpo.update(extra)
        return cuerpo


async def montar(
    session: AsyncSession,
    rol_veterinario: Role = Role.VETERINARIAN,
    con_agenda: bool = True,
) -> Escenario:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=rol_veterinario))
    await session.flush()

    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=cliente.id or 0))

    if con_agenda:
        slots = SqlAlchemyAvailabilityRepository(session)
        await slots.add(
            AvailabilitySlot(
                veterinarian_id=veterinario.id or 0,
                starts_at=JORNADA,
                ends_at=JORNADA + timedelta(hours=8),
            )
        )
    await session.commit()
    return Escenario(cliente, mascota, veterinario)


async def test_los_motivos_reservables_excluyen_la_emergencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    """El original escribia `WHERE id != 8` en cada consulta."""
    escenario = await montar(session)

    response = await client.get(f"{URL}/types", headers=authorization_for(escenario.cliente))

    assert response.status_code == 200
    nombres = [item["name"] for item in response.json()["items"]]
    assert "Emergencia" not in nombres
    assert "Consulta general" in nombres


async def test_un_cliente_reserva_una_cita(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["client_id"] == escenario.cliente.id
    assert body["duration_minutes"] == 30


async def test_no_se_puede_reservar_con_la_mascota_de_otro(
    client: AsyncClient, session: AsyncSession
) -> None:
    """El original recibia el id del cliente en el cuerpo y no comprobaba nada."""
    escenario = await montar(session)
    users = SqlAlchemyUserRepository(session)
    intruso = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.post(URL, json=escenario.reserva(), headers=authorization_for(intruso))

    assert response.status_code == 404


async def test_no_se_puede_reservar_fuera_de_la_agenda(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json=escenario.reserva(scheduled_at=(JORNADA + timedelta(hours=20)).isoformat()),
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 409
    assert "disponibilidad" in response.json()["detail"]


async def test_una_cita_que_se_pasa_del_tramo_no_entra(
    client: AsyncClient, session: AsyncSession
) -> None:
    """La cirugia dura noventa minutos y la jornada termina antes."""
    escenario = await montar(session)

    response = await client.post(
        URL,
        json=escenario.reserva(
            appointment_type_id=SURGERY_TYPE_ID,
            scheduled_at=(JORNADA + timedelta(hours=7, minutes=30)).isoformat(),
        ),
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    ("desplazamiento_minutos", "esperado"),
    [(0, 409), (20, 409), (35, 409), (45, 201), (-45, 201)],
)
async def test_el_solapamiento_respeta_el_margen_de_diez_minutos(
    client: AsyncClient,
    session: AsyncSession,
    desplazamiento_minutos: int,
    esperado: int,
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    primera = await client.post(URL, json=escenario.reserva(), headers=cabeceras)
    assert primera.status_code == 201

    segunda = await client.post(
        URL,
        json=escenario.reserva(
            scheduled_at=(HORA + timedelta(minutes=desplazamiento_minutos)).isoformat()
        ),
        headers=cabeceras,
    )

    assert segunda.status_code == esperado


async def test_una_cita_cancelada_libera_el_hueco(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    primera = await client.post(URL, json=escenario.reserva(), headers=cabeceras)
    cita_id = primera.json()["id"]

    await client.post(
        f"{URL}/{cita_id}/cancel", json={"reason": "Se me cruzo un viaje"}, headers=cabeceras
    )
    repetida = await client.post(URL, json=escenario.reserva(), headers=cabeceras)

    assert repetida.status_code == 201


async def test_la_emergencia_no_se_reserva_con_antelacion(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json=escenario.reserva(appointment_type_id=EMERGENCY_TYPE_ID),
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 422


async def test_el_personal_no_reserva_citas(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.veterinario)
    )

    assert response.status_code == 403


async def test_el_veterinario_confirma_y_completa(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )
    cita_id = creada.json()["id"]
    cabeceras = authorization_for(escenario.veterinario)

    confirmada = await client.post(f"{URL}/{cita_id}/confirm", headers=cabeceras)
    completada = await client.post(f"{URL}/{cita_id}/complete", headers=cabeceras)

    assert confirmada.json()["status"] == "confirmed"
    assert completada.json()["status"] == "completed"
    assert completada.json()["updated_by"] == escenario.veterinario.id


async def test_un_cliente_no_confirma_su_propia_cita(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )

    response = await client.post(
        f"{URL}/{creada.json()['id']}/confirm",
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_una_cita_completada_no_se_cancela(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )
    cita_id = creada.json()["id"]
    vet = authorization_for(escenario.veterinario)
    await client.post(f"{URL}/{cita_id}/confirm", headers=vet)
    await client.post(f"{URL}/{cita_id}/complete", headers=vet)

    response = await client.post(
        f"{URL}/{cita_id}/cancel",
        json={"reason": "Me arrepenti"},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 409


async def test_cancelar_exige_razon(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )

    response = await client.post(
        f"{URL}/{creada.json()['id']}/cancel",
        json={"reason": ""},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 422


async def test_una_cita_ajena_no_existe(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )
    users = SqlAlchemyUserRepository(session)
    intruso = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.post(
        f"{URL}/{creada.json()['id']}/cancel",
        json={"reason": "Porque si"},
        headers=authorization_for(intruso),
    )

    assert response.status_code == 404


async def test_cada_rol_ve_su_recorte_del_listado(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await client.post(URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente))
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    del_cliente = await client.get(URL, headers=authorization_for(escenario.cliente))
    del_veterinario = await client.get(URL, headers=authorization_for(escenario.veterinario))
    del_ajeno = await client.get(URL, headers=authorization_for(otro))

    assert del_cliente.json()["total"] == 1
    assert del_veterinario.json()["total"] == 1
    assert del_ajeno.json()["total"] == 0


async def test_un_cliente_no_puede_ampliar_el_listado_con_un_filtro(
    client: AsyncClient, session: AsyncSession
) -> None:
    """El recorte se aplica sobre el criterio, no sobre el resultado."""
    escenario = await montar(session)
    await client.post(URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente))
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.get(
        URL,
        params={"client_id": escenario.cliente.id},
        headers=authorization_for(otro),
    )

    assert response.json()["total"] == 0


async def test_la_emergencia_asigna_al_veterinario_de_guardia(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session, rol_veterinario=Role.EMERGENCY_VETERINARIAN)
    # La guardia tiene que cubrir el momento presente, no una fecha futura.
    slots = SqlAlchemyAvailabilityRepository(session)
    ahora = datetime.now(UTC)
    await slots.add(
        AvailabilitySlot(
            veterinarian_id=escenario.veterinario.id or 0,
            starts_at=ahora - timedelta(hours=1),
            ends_at=ahora + timedelta(hours=7),
        )
    )
    await session.commit()

    response = await client.post(
        f"{URL}/emergency",
        json={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["veterinarian_id"] == escenario.veterinario.id
    assert body["description"] == "Cita de emergencia"


async def test_sin_veterinario_de_guardia_la_emergencia_lo_dice(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session, rol_veterinario=Role.EMERGENCY_VETERINARIAN)

    response = await client.post(
        f"{URL}/emergency",
        json={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 409
    assert "telefono" in response.json()["detail"] or "teléfono" in response.json()["detail"]


async def test_un_veterinario_comun_no_atiende_emergencias(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Solo el rol de emergencia entra en el reparto automatico."""
    escenario = await montar(session, rol_veterinario=Role.VETERINARIAN)
    slots = SqlAlchemyAvailabilityRepository(session)
    ahora = datetime.now(UTC)
    await slots.add(
        AvailabilitySlot(
            veterinarian_id=escenario.veterinario.id or 0,
            starts_at=ahora - timedelta(hours=1),
            ends_at=ahora + timedelta(hours=7),
        )
    )
    await session.commit()

    response = await client.post(
        f"{URL}/emergency",
        json={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 409

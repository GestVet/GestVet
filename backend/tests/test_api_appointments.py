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

from gestvet.core.clinic_time import clinic_day_window
from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.appointments.adapters.persistence.models import AppointmentRow
from gestvet.modules.appointments.adapters.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
)
from gestvet.modules.appointments.domain.entities import Appointment
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
    SURGERY_TYPE_ID,
    authorization_for,
    build_pet,
    build_user,
)

URL = "/api/v1/appointments"
# Mañana a las 9 UTC: una fecha fija del calendario vuelve pasada la cita en
# cuanto llega ese día, y la inasistencia se calcula sola contra el reloj real.
JORNADA = (datetime.now(UTC) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
HORA = JORNADA + timedelta(hours=1)


async def _ya_empezo(session: AsyncSession, cita_id: int) -> None:
    """Lleva la cita a hace diez minutos, para poder cerrarla."""
    fila = await session.get(AppointmentRow, cita_id)
    assert fila is not None
    fila.scheduled_at = datetime.now(UTC) - timedelta(minutes=10)
    await session.commit()


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
    await _ya_empezo(session, cita_id)
    completada = await client.post(f"{URL}/{cita_id}/complete", headers=cabeceras)

    assert confirmada.json()["status"] == "confirmed"
    assert completada.json()["status"] == "completed"
    assert completada.json()["updated_by"] == escenario.veterinario.id


async def test_el_veterinario_marca_la_inasistencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )
    cita_id = creada.json()["id"]
    cabeceras = authorization_for(escenario.veterinario)
    await client.post(f"{URL}/{cita_id}/confirm", headers=cabeceras)
    await _ya_empezo(session, cita_id)

    respuesta = await client.post(f"{URL}/{cita_id}/no-show", headers=cabeceras)

    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "no_show"
    assert respuesta.json()["status_label"] == "No asistió"


async def test_un_cliente_no_marca_su_propia_inasistencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )
    cita_id = creada.json()["id"]
    await client.post(f"{URL}/{cita_id}/confirm", headers=authorization_for(escenario.veterinario))

    respuesta = await client.post(
        f"{URL}/{cita_id}/no-show", headers=authorization_for(escenario.cliente)
    )

    assert respuesta.status_code == 403


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
    await _ya_empezo(session, cita_id)
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


def _turno_de_ahora(ahora: datetime) -> tuple[datetime, datetime]:
    """Un turno de atención que cubre este momento sin cruzar la medianoche."""
    inicio_del_dia, fin_del_dia = clinic_day_window(ahora)
    return max(inicio_del_dia, ahora - timedelta(minutes=30)), min(
        fin_del_dia, ahora + timedelta(hours=3)
    )


async def _guardia_ahora(session: AsyncSession, veterinario_id: int, ahora: datetime) -> None:
    await SqlAlchemyAvailabilityRepository(session).add(
        AvailabilitySlot(
            veterinarian_id=veterinario_id,
            starts_at=ahora - timedelta(hours=1),
            ends_at=ahora + timedelta(hours=11),
            kind=ShiftKind.ON_CALL,
        )
    )
    await session.commit()


async def _atencion_ahora(session: AsyncSession, veterinario_id: int, ahora: datetime) -> None:
    inicio, fin = _turno_de_ahora(ahora)
    await SqlAlchemyAvailabilityRepository(session).add(
        AvailabilitySlot(veterinarian_id=veterinario_id, starts_at=inicio, ends_at=fin)
    )
    await session.commit()


async def test_la_emergencia_asigna_al_veterinario_de_guardia(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session, con_agenda=False)
    await _guardia_ahora(session, escenario.veterinario.id or 0, datetime.now(UTC))

    response = await client.post(
        f"{URL}/emergency",
        json={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["veterinarian_id"] == escenario.veterinario.id
    assert body["description"] == "Cita de emergencia"


async def test_sin_nadie_de_guardia_ni_en_turno_la_emergencia_lo_dice(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session, con_agenda=False)

    response = await client.post(
        f"{URL}/emergency",
        json={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 409
    assert "telefono" in response.json()["detail"] or "teléfono" in response.json()["detail"]


async def test_una_guardia_no_se_ofrece_para_citas_normales(
    client: AsyncClient, session: AsyncSession
) -> None:
    """HU09: la guardia cubre emergencias; reservar exige un turno de atención."""
    escenario = await montar(session, con_agenda=False)
    await SqlAlchemyAvailabilityRepository(session).add(
        AvailabilitySlot(
            veterinarian_id=escenario.veterinario.id or 0,
            starts_at=JORNADA,
            ends_at=JORNADA + timedelta(hours=8),
            kind=ShiftKind.ON_CALL,
        )
    )
    await session.commit()

    response = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )

    assert response.status_code == 409


async def test_con_la_guardia_ocupada_cubre_un_veterinario_de_turno_libre(
    client: AsyncClient, session: AsyncSession
) -> None:
    """HU10: en vez de amontonar en el mismo, cubre quien atiende y está libre."""
    escenario = await montar(session, con_agenda=False)
    ahora = datetime.now(UTC)
    await _guardia_ahora(session, escenario.veterinario.id or 0, ahora)
    users = SqlAlchemyUserRepository(session)
    de_turno = await users.add(build_user("turno@example.com", role=Role.VETERINARIAN))
    await session.commit()
    await _atencion_ahora(session, de_turno.id or 0, ahora)
    cabeceras = authorization_for(escenario.cliente)

    primera = await client.post(
        f"{URL}/emergency", json={"pet_id": escenario.mascota.id}, headers=cabeceras
    )
    assert primera.status_code == 201
    assert primera.json()["veterinarian_id"] == escenario.veterinario.id

    otro_cliente = await users.add(build_user("beto@example.com"))
    otra_mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=otro_cliente.id or 0, name="Luna")
    )
    await session.commit()

    segunda = await client.post(
        f"{URL}/emergency",
        json={"pet_id": otra_mascota.id},
        headers=authorization_for(otro_cliente),
    )

    assert segunda.status_code == 201
    assert segunda.json()["veterinarian_id"] == de_turno.id


async def test_el_dia_que_bloquea_al_que_cubre_es_el_dia_local_no_el_utc(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Regresión de un bug encontrado a mano.

    Una emergencia tarde en la noche (hora de Trujillo) cae del otro lado de
    la medianoche en UTC. Compararlas por fecha calendario UTC dejaba pasar
    una cita normal más temprano ese mismo día local.
    """
    escenario = await montar(session, con_agenda=False)
    slots = SqlAlchemyAvailabilityRepository(session)
    await slots.add(
        AvailabilitySlot(
            veterinarian_id=escenario.veterinario.id or 0,
            starts_at=datetime(2026, 9, 13, 13, 0, tzinfo=UTC),
            ends_at=datetime(2026, 9, 13, 20, 0, tzinfo=UTC),
        )
    )
    appointments = SqlAlchemyAppointmentRepository(session)
    await appointments.add(
        Appointment(
            scheduled_at=datetime(2026, 9, 14, 4, 0, tzinfo=UTC),
            duration=timedelta(hours=1),
            client_id=escenario.cliente.id or 0,
            pet_id=escenario.mascota.id or 0,
            veterinarian_id=escenario.veterinario.id or 0,
            appointment_type_id=EMERGENCY_TYPE_ID,
        )
    )
    await session.commit()

    intento = await client.post(
        URL,
        json=escenario.reserva(scheduled_at=datetime(2026, 9, 13, 14, 0, tzinfo=UTC).isoformat()),
        headers=authorization_for(escenario.cliente),
    )

    assert intento.status_code == 409


async def test_quien_cubre_una_emergencia_no_recibe_citas_normales_ese_dia(
    client: AsyncClient, session: AsyncSession
) -> None:
    """HU10: cubrir una emergencia bloquea sus citas normales por el resto del día."""
    escenario = await montar(session, con_agenda=False)
    ahora = datetime.now(UTC)
    await _atencion_ahora(session, escenario.veterinario.id or 0, ahora)

    abierta = await client.post(
        f"{URL}/emergency",
        json={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )
    assert abierta.status_code == 201
    assert abierta.json()["veterinarian_id"] == escenario.veterinario.id

    intento = await client.post(
        URL,
        json=escenario.reserva(scheduled_at=(ahora + timedelta(hours=1)).isoformat()),
        headers=authorization_for(escenario.cliente),
    )

    assert intento.status_code == 409


async def test_un_veterinario_fuera_de_turno_no_atiende_emergencias(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Solo entra en el reparto quien está de guardia o en turno ahora."""
    escenario = await montar(session, con_agenda=False)
    inicio_de_manana, _ = clinic_day_window(datetime.now(UTC) + timedelta(days=1))
    await SqlAlchemyAvailabilityRepository(session).add(
        AvailabilitySlot(
            veterinarian_id=escenario.veterinario.id or 0,
            starts_at=inicio_de_manana + timedelta(hours=9),
            ends_at=inicio_de_manana + timedelta(hours=17),
        )
    )
    await session.commit()

    response = await client.post(
        f"{URL}/emergency",
        json={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 409


async def test_no_se_completa_una_cita_de_manana(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )
    cita_id = creada.json()["id"]
    cabeceras = authorization_for(escenario.veterinario)
    await client.post(f"{URL}/{cita_id}/confirm", headers=cabeceras)

    completar = await client.post(f"{URL}/{cita_id}/complete", headers=cabeceras)
    inasistencia = await client.post(f"{URL}/{cita_id}/no-show", headers=cabeceras)

    assert completar.status_code == 409
    assert "todavía no empezó" in completar.json()["detail"]
    assert inasistencia.status_code == 409
    listado = await client.get(URL, headers=cabeceras)
    assert listado.json()["items"][0]["status"] == "confirmed"


async def test_la_cita_dice_desde_cuando_se_puede_cerrar(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )

    body = creada.json()
    assert datetime.fromisoformat(body["completable_from"]) == HORA - timedelta(minutes=30)
    assert datetime.fromisoformat(body["no_show_from"]) == HORA


async def test_la_cita_trae_los_nombres_para_mostrarla(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    creada = await client.post(
        URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
    )

    body = creada.json()
    assert body["pet_name"] == "Rocco"
    assert body["client_name"] == "Ana Quispe"
    assert body["veterinarian_name"] == "Ana Quispe"
    assert body["appointment_type_name"] == "Consulta general"
    assert body["is_emergency"] is False


async def test_el_listado_trae_los_nombres_de_cada_cita(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await client.post(URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente))
    await client.post(
        URL,
        json=escenario.reserva(scheduled_at=(HORA + timedelta(hours=2)).isoformat()),
        headers=authorization_for(escenario.cliente),
    )

    for quien in (escenario.cliente, escenario.veterinario):
        response = await client.get(URL, headers=authorization_for(quien))
        items = response.json()["items"]
        assert len(items) == 2
        assert {item["pet_name"] for item in items} == {"Rocco"}
        assert {item["appointment_type_name"] for item in items} == {"Consulta general"}
        assert all(item["client_name"] == "Ana Quispe" for item in items)


async def test_la_emergencia_se_muestra_como_tal(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session, con_agenda=False)
    await _guardia_ahora(session, escenario.veterinario.id or 0, datetime.now(UTC))

    response = await client.post(
        f"{URL}/emergency",
        json={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.json()["is_emergency"] is True
    assert response.json()["appointment_type_name"] == "Emergencia"

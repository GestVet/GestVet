"""Pruebas del adaptador HTTP de los consentimientos que pide el veterinario.

Recorren la aplicación entera contra una base real, incluida la lectura hacia
las tablas de citas, mascotas y cuentas.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.core.realtime import CONSENTS_TOPIC
from gestvet.core.realtime_broker import LocalBroker
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.appointments.adapters.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
)
from gestvet.modules.appointments.domain.entities import Appointment
from gestvet.modules.consents.adapters.persistence.models import ConsentRow
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

URL = "/api/v1/consents"
INTERNACIONES = "/api/v1/hospitalizations"
HORA = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)
JUSTIFICACION = "Paro respiratorio; el responsable no contesta el teléfono."
FIRMA = {"signer_name": "Ana Quispe", "accepted": True}


class Clinica:
    def __init__(
        self,
        cliente: User,
        intruso: User,
        veterinario: User,
        otro_veterinario: User,
        admin: User,
        pet_id: int,
        cita_id: int,
        emergencia_id: int,
    ) -> None:
        self.cliente = cliente
        self.intruso = intruso
        self.veterinario = veterinario
        self.otro_veterinario = otro_veterinario
        self.admin = admin
        self.pet_id = pet_id
        self.cita_id = cita_id
        self.emergencia_id = emergencia_id


async def montar(session: AsyncSession) -> Clinica:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    intruso = await users.add(build_user("beto@example.com", first_name="Beto"))
    veterinario = await users.add(
        build_user("vet@example.com", role=Role.VETERINARIAN, first_name="Rosa", last_name="Díaz")
    )
    otro = await users.add(build_user("otro@example.com", role=Role.VETERINARIAN))
    admin = await users.add(build_user("admin@example.com", role=Role.ADMIN))
    await session.flush()
    mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=cliente.id or 0, name="Firulais")
    )
    citas = SqlAlchemyAppointmentRepository(session)

    async def cita(tipo: int, hora: datetime) -> int:
        guardada = await citas.add(
            Appointment(
                scheduled_at=hora,
                duration=timedelta(minutes=30),
                client_id=cliente.id or 0,
                pet_id=mascota.id or 0,
                veterinarian_id=veterinario.id or 0,
                appointment_type_id=tipo,
            )
        )
        return guardada.id or 0

    normal = await cita(GENERAL_TYPE_ID, HORA)
    emergencia = await cita(EMERGENCY_TYPE_ID, HORA + timedelta(hours=2))
    await session.commit()
    return Clinica(cliente, intruso, veterinario, otro, admin, mascota.id or 0, normal, emergencia)


async def pedir(
    client: AsyncClient, clinica: Clinica, kind: str = "procedure", **extra: object
) -> dict[str, object]:
    cuerpo: dict[str, object] = {
        "appointment_id": clinica.cita_id,
        "kind": kind,
        "details": {"procedure": "Castración", "estimated_cost": "450.5"},
    }
    cuerpo.update(extra)
    response = await client.post(URL, json=cuerpo, headers=authorization_for(clinica.veterinario))
    assert response.status_code == 201, response.text
    return response.json()


async def test_el_veterinario_pide_y_avisa_al_cliente(
    client: AsyncClient, session: AsyncSession, broker: LocalBroker
) -> None:
    clinica = await montar(session)

    async with broker.subscribe() as queue:
        body = await pedir(client, clinica)
        event = queue.get_nowait()

    assert body["status"] == "pending"
    assert body["status_label"] == "Pendiente"
    assert body["channel"] is None and body["signer_name"] is None
    assert body["pet_name"] == "Firulais"
    assert body["requested_by_name"] == "Rosa Díaz"
    assert body["details"]["estimated_cost"] == "450.50"
    assert "- Procedimiento: Castración" in body["text_snapshot"]
    assert "S/ 450.50" in body["text_snapshot"]
    assert body["expires_at"] is not None
    assert event.topic == CONSENTS_TOPIC
    assert event.user_ids == frozenset({clinica.cliente.id, clinica.veterinario.id})


async def test_pedir_exige_el_permiso_y_la_cita_propia(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    cuerpo = {"appointment_id": clinica.cita_id, "kind": "hospitalization"}

    como_cliente = await client.post(URL, json=cuerpo, headers=authorization_for(clinica.cliente))
    ajena = await client.post(URL, json=cuerpo, headers=authorization_for(clinica.otro_veterinario))
    sin_procedimiento = await client.post(
        URL,
        json={**cuerpo, "kind": "euthanasia"},
        headers=authorization_for(clinica.veterinario),
    )
    riesgo = await client.post(
        URL,
        json={**cuerpo, "kind": "emergency_risk"},
        headers=authorization_for(clinica.veterinario),
    )

    assert como_cliente.status_code == 403
    assert ajena.status_code == 404
    assert sin_procedimiento.status_code == 422
    assert "procedimiento" in sin_procedimiento.json()["detail"]
    assert riesgo.status_code == 422


async def test_el_cliente_ve_sus_pendientes_y_acepta(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    pedido = await pedir(client, clinica)

    pendientes = await client.get(
        URL, params={"status": "pending"}, headers=authorization_for(clinica.cliente)
    )
    ajenos = await client.get(URL, headers=authorization_for(clinica.intruso))
    assert [item["id"] for item in pendientes.json()["items"]] == [pedido["id"]]
    assert ajenos.json()["items"] == []

    response = await client.post(
        f"{URL}/{pedido['id']}/accept",
        json={"signer_name": "  Ana   Quispe ", "accepted": True},
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "accepted"
    assert body["channel"] == "online"
    assert body["signer_name"] == "Ana Quispe"
    assert body["text_snapshot"] == pedido["text_snapshot"]
    otra_vez = await client.post(
        f"{URL}/{pedido['id']}/accept", json=FIRMA, headers=authorization_for(clinica.cliente)
    )
    assert otra_vez.status_code == 409


async def test_aceptar_exige_la_casilla_y_ser_el_dueno(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    pedido = await pedir(client, clinica)
    ruta = f"{URL}/{pedido['id']}/accept"

    sin_casilla = await client.post(
        ruta, json={**FIRMA, "accepted": False}, headers=authorization_for(clinica.cliente)
    )
    ajeno = await client.post(ruta, json=FIRMA, headers=authorization_for(clinica.intruso))
    veterinario = await client.post(
        ruta, json=FIRMA, headers=authorization_for(clinica.veterinario)
    )
    una_palabra = await client.post(
        ruta, json={**FIRMA, "signer_name": "Ana"}, headers=authorization_for(clinica.cliente)
    )

    assert sin_casilla.status_code == 422
    assert ajeno.status_code == 404
    assert veterinario.status_code == 403
    assert una_palabra.status_code == 422


async def test_un_pedido_vencido_sale_vencido_y_no_se_acepta(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    pedido = await pedir(client, clinica)
    await session.execute(
        update(ConsentRow)
        .where(ConsentRow.id == pedido["id"])
        .values(created_at=datetime.now(UTC) - timedelta(hours=25))
    )
    await session.commit()

    leido = await client.get(f"{URL}/{pedido['id']}", headers=authorization_for(clinica.cliente))
    pendientes = await client.get(
        URL, params={"status": "pending"}, headers=authorization_for(clinica.cliente)
    )
    aceptar = await client.post(
        f"{URL}/{pedido['id']}/accept", json=FIRMA, headers=authorization_for(clinica.cliente)
    )

    assert leido.json()["status"] == "expired"
    assert pendientes.json()["items"] == []
    assert aceptar.status_code == 409
    assert "venció" in aceptar.json()["detail"]


async def test_el_cliente_rechaza_y_la_internacion_queda_bloqueada(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    pedido = await pedir(client, clinica, "hospitalization", details={})

    rechazo = await client.post(
        f"{URL}/{pedido['id']}/decline",
        json={"reason": "Prefiero llevarla a casa"},
        headers=authorization_for(clinica.cliente),
    )
    internar = await client.post(
        INTERNACIONES,
        json={"appointment_id": clinica.cita_id, "reason": "Observación por 48 horas"},
        headers=authorization_for(clinica.veterinario),
    )

    assert rechazo.status_code == 200
    assert rechazo.json()["status"] == "declined"
    assert rechazo.json()["decision_reason"] == "Prefiero llevarla a casa"
    assert internar.status_code == 409
    assert "consentimiento de internación" in internar.json()["detail"]


async def test_la_firma_en_persona_deja_al_veterinario_de_testigo_y_habilita_internar(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    pedido = await pedir(client, clinica, "hospitalization", details={})

    ajeno = await client.post(
        f"{URL}/{pedido['id']}/accept-in-person",
        json=FIRMA,
        headers=authorization_for(clinica.otro_veterinario),
    )
    firmado = await client.post(
        f"{URL}/{pedido['id']}/accept-in-person",
        json=FIRMA,
        headers=authorization_for(clinica.veterinario),
    )
    internar = await client.post(
        INTERNACIONES,
        json={"appointment_id": clinica.cita_id, "reason": "Observación por 48 horas"},
        headers=authorization_for(clinica.veterinario),
    )

    assert ajeno.status_code == 404
    assert firmado.status_code == 200
    body = firmado.json()
    assert body["channel"] == "in_person"
    assert body["witness_id"] == clinica.veterinario.id
    assert body["witness_name"] == "Rosa Díaz"
    assert internar.status_code == 201


async def test_la_urgencia_vital_solo_en_emergencias_y_habilita_internar(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    cuerpo = {"kind": "hospitalization", "justification": JUSTIFICACION}
    vet = authorization_for(clinica.veterinario)

    en_cita_normal = await client.post(
        f"{URL}/waive", json={**cuerpo, "appointment_id": clinica.cita_id}, headers=vet
    )
    corta = await client.post(
        f"{URL}/waive",
        json={**cuerpo, "appointment_id": clinica.emergencia_id, "justification": "Urgente"},
        headers=vet,
    )
    como_cliente = await client.post(
        f"{URL}/waive",
        json={**cuerpo, "appointment_id": clinica.emergencia_id},
        headers=authorization_for(clinica.cliente),
    )
    eximido = await client.post(
        f"{URL}/waive", json={**cuerpo, "appointment_id": clinica.emergencia_id}, headers=vet
    )
    internar = await client.post(
        INTERNACIONES,
        json={"appointment_id": clinica.emergencia_id, "reason": "Shock, queda en observación"},
        headers=vet,
    )

    assert en_cita_normal.status_code == 409
    assert "emergencia" in en_cita_normal.json()["detail"]
    assert corta.status_code == 422
    assert como_cliente.status_code == 403
    assert eximido.status_code == 201
    assert eximido.json()["status"] == "waived_emergency"
    assert eximido.json()["status_label"] == "Sin consentimiento por urgencia vital"
    assert eximido.json()["decision_reason"] == JUSTIFICACION
    assert internar.status_code == 201


async def test_el_listado_de_una_cita_es_para_quien_la_atiende(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    await pedir(client, clinica)
    params = {"appointment_id": clinica.cita_id}

    propio = await client.get(URL, params=params, headers=authorization_for(clinica.veterinario))
    admin = await client.get(URL, params=params, headers=authorization_for(clinica.admin))
    ajeno = await client.get(
        URL, params=params, headers=authorization_for(clinica.otro_veterinario)
    )
    sin_cita = await client.get(URL, headers=authorization_for(clinica.veterinario))

    assert len(propio.json()["items"]) == 1
    assert propio.json()["appointment_is_emergency"] is False
    assert len(admin.json()["items"]) == 1
    assert ajeno.status_code == 404
    assert sin_cita.status_code == 422


async def test_el_texto_vigente_de_un_tipo_nuevo_lo_lee_el_veterinario(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.get(
        f"{URL}/templates/current",
        params={"kind": "euthanasia"},
        headers=authorization_for(clinica.veterinario),
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "euthanasia"
    assert "voluntaria" in response.json()["body"]

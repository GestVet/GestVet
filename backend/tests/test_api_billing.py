"""Pruebas del adaptador HTTP de los pagos.

Recorren la aplicación entera contra una base real, incluida la lectura hacia
la tabla de citas para completar el cliente de cada pago.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

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

URL = "/api/v1/payments"
HORA = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)

PAGO = {"amount": "60.00", "method": "cash"}


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


async def test_el_personal_registra_un_pago(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**PAGO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "60.00"
    assert body["method"] == "cash"
    assert body["method_label"] == "Efectivo"
    assert body["client_id"] == escenario.cliente.id
    assert body["is_voided"] is False


async def test_un_cliente_no_puede_registrar_un_pago(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**PAGO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_no_se_puede_pagar_una_cita_inexistente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**PAGO, "appointment_id": 999},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 404


async def test_el_monto_debe_ser_positivo(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={**PAGO, "appointment_id": escenario.cita_id, "amount": "0"},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 422


async def test_el_cliente_ve_sus_propios_pagos(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    await client.post(
        URL,
        json={**PAGO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.veterinario),
    )

    response = await client.get(URL, headers=authorization_for(escenario.cliente))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["appointment_id"] == escenario.cita_id


async def test_un_cliente_no_ve_pagos_de_otro(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    await client.post(
        URL,
        json={**PAGO, "appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.veterinario),
    )
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.get(URL, headers=authorization_for(otro))

    assert response.status_code == 200
    assert response.json()["total"] == 0


async def test_anular_un_pago(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.veterinario)
    creado = await client.post(
        URL, json={**PAGO, "appointment_id": escenario.cita_id}, headers=cabeceras
    )
    pago_id = creado.json()["id"]

    response = await client.post(
        f"{URL}/{pago_id}/void",
        json={"reason": "Se cargó el monto equivocado"},
        headers=cabeceras,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_voided"] is True
    assert body["void_reason"] == "Se cargó el monto equivocado"


async def test_no_se_puede_anular_dos_veces(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.veterinario)
    creado = await client.post(
        URL, json={**PAGO, "appointment_id": escenario.cita_id}, headers=cabeceras
    )
    pago_id = creado.json()["id"]
    await client.post(f"{URL}/{pago_id}/void", json={"reason": "Motivo"}, headers=cabeceras)

    response = await client.post(
        f"{URL}/{pago_id}/void", json={"reason": "Otro motivo"}, headers=cabeceras
    )

    assert response.status_code == 409


async def test_anular_exige_motivo(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.veterinario)
    creado = await client.post(
        URL, json={**PAGO, "appointment_id": escenario.cita_id}, headers=cabeceras
    )
    pago_id = creado.json()["id"]

    response = await client.post(f"{URL}/{pago_id}/void", json={"reason": ""}, headers=cabeceras)

    assert response.status_code == 422


async def test_el_reporte_solo_lo_ve_administracion(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.get(f"{URL}/report", headers=authorization_for(escenario.veterinario))

    assert response.status_code == 403


async def test_el_reporte_agrupa_por_metodo_y_excluye_anulados(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    users = SqlAlchemyUserRepository(session)
    jefa = await users.add(build_user("jefa@example.com", role=Role.ADMIN))
    await session.commit()
    cabeceras_vet = authorization_for(escenario.veterinario)

    primero = await client.post(
        URL, json={**PAGO, "appointment_id": escenario.cita_id}, headers=cabeceras_vet
    )
    await client.post(
        URL,
        json={"appointment_id": escenario.cita_id, "amount": "40.00", "method": "cash"},
        headers=cabeceras_vet,
    )
    anulado = await client.post(
        URL,
        json={"appointment_id": escenario.cita_id, "amount": "999.00", "method": "yape"},
        headers=cabeceras_vet,
    )
    await client.post(
        f"{URL}/{anulado.json()['id']}/void",
        json={"reason": "Se cargó por error"},
        headers=cabeceras_vet,
    )
    assert primero.status_code == 201

    response = await client.get(f"{URL}/report", headers=authorization_for(jefa))

    assert response.status_code == 200
    body = response.json()
    montos = {item["method"]: Decimal(item["total"]) for item in body["items"]}
    assert montos["cash"] == Decimal("100.00")
    assert "yape" not in montos
    assert Decimal(body["grand_total"]) == Decimal("100.00")

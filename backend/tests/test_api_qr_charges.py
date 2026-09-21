"""Pruebas del adaptador HTTP de los cobros por QR.

Recorren la aplicación entera contra una base real, con el adaptador sandbox
de la pasarela de pago (no hay banco real de por medio).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.config import get_settings
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
from tests.conftest import (
    EMERGENCY_TYPE_ID,
    GENERAL_TYPE_ID,
    authorization_for,
    build_pet,
    build_user,
)

PAYMENTS_URL = "/api/v1/payments"
QR_URL = f"{PAYMENTS_URL}/qr-charges"
HORA = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def simulacion_del_banco(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Las pruebas de confirmación no dependen del `DEBUG` del `.env` local."""
    monkeypatch.setenv("QR_SIMULATION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _apagar_simulacion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QR_SIMULATION_ENABLED", "false")
    get_settings.cache_clear()


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
    # El QR solo se genera después de la atención: la mayoría de las
    # pruebas de este archivo asumen una cita ya completada.
    cita.confirm(veterinario.id or 0)
    cita.complete(veterinario.id or 0)
    cita = await appointments.save(cita)
    await session.commit()
    return Escenario(cliente, veterinario, cita.id or 0)


async def montar_emergencia(session: AsyncSession) -> Escenario:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("carmen@example.com"))
    veterinario = await users.add(build_user("guardia@example.com", role=Role.VETERINARIAN))
    await session.flush()

    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=cliente.id or 0))

    appointments = SqlAlchemyAppointmentRepository(session)
    cita = await appointments.add(
        Appointment(
            scheduled_at=HORA,
            duration=timedelta(minutes=60),
            client_id=cliente.id or 0,
            pet_id=mascota.id or 0,
            veterinarian_id=veterinario.id or 0,
            appointment_type_id=EMERGENCY_TYPE_ID,
        )
    )
    cita.confirm(veterinario.id or 0)
    cita.complete(veterinario.id or 0)
    cita = await appointments.save(cita)
    await session.commit()
    return Escenario(cliente, veterinario, cita.id or 0)


async def test_el_cliente_genera_un_qr_para_su_propia_cita(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 201
    body = response.json()
    assert Decimal(body["amount"]) == Decimal("60.00")
    assert body["status"] == "pending"
    assert body["status_label"] == "Pendiente"
    assert body["qr_image_data_url"].startswith("data:image/png;base64,")


async def test_el_personal_tambien_genera_un_qr(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 201


async def test_un_cliente_no_genera_un_qr_de_una_cita_ajena(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.post(
        QR_URL, json={"appointment_id": escenario.cita_id}, headers=authorization_for(otro)
    )

    assert response.status_code == 404


async def test_no_se_genera_un_qr_de_una_cita_inexistente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        QR_URL, json={"appointment_id": 999}, headers=authorization_for(escenario.veterinario)
    )

    assert response.status_code == 404


async def test_no_se_genera_un_qr_de_una_cita_no_completada(
    client: AsyncClient, session: AsyncSession
) -> None:
    """El precio es fijo: solo corresponde una vez que se sabe qué se atendió."""
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("carmen@example.com"))
    veterinario = await users.add(build_user("vet2@example.com", role=Role.VETERINARIAN))
    await session.flush()
    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=cliente.id or 0))
    appointments = SqlAlchemyAppointmentRepository(session)
    cita_pendiente = await appointments.add(
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

    response = await client.post(
        QR_URL,
        json={"appointment_id": cita_pendiente.id},
        headers=authorization_for(cliente),
    )

    assert response.status_code == 409


async def test_generar_dos_veces_devuelve_el_mismo_cobro_pendiente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)

    primero = await client.post(
        QR_URL, json={"appointment_id": escenario.cita_id}, headers=cabeceras
    )
    segundo = await client.post(
        QR_URL, json={"appointment_id": escenario.cita_id}, headers=cabeceras
    )

    assert primero.json()["id"] == segundo.json()["id"]


async def test_el_cliente_consulta_el_estado_de_su_cobro(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    creado = await client.post(
        QR_URL, json={"appointment_id": escenario.cita_id}, headers=cabeceras
    )
    charge_id = creado.json()["id"]

    response = await client.get(f"{QR_URL}/{charge_id}", headers=cabeceras)

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


async def test_un_cliente_no_consulta_el_cobro_de_otro(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creado = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )
    charge_id = creado.json()["id"]
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.get(f"{QR_URL}/{charge_id}", headers=authorization_for(otro))

    assert response.status_code == 404


async def test_confirmar_el_cobro_crea_un_pago(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    creado = await client.post(
        QR_URL, json={"appointment_id": escenario.cita_id}, headers=cabeceras
    )
    charge_id = creado.json()["id"]

    response = await client.post(f"{QR_URL}/{charge_id}/confirm", headers=cabeceras)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "paid"
    assert body["payment_id"] is not None

    pagos = await client.get(
        PAYMENTS_URL, params={"appointment_id": escenario.cita_id}, headers=cabeceras
    )
    items = pagos.json()["items"]
    assert len(items) == 1
    assert items[0]["method"] == "qr"
    assert Decimal(items[0]["amount"]) == Decimal("60.00")


async def test_no_se_confirma_un_cobro_ya_pagado(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    creado = await client.post(
        QR_URL, json={"appointment_id": escenario.cita_id}, headers=cabeceras
    )
    charge_id = creado.json()["id"]
    await client.post(f"{QR_URL}/{charge_id}/confirm", headers=cabeceras)

    response = await client.post(f"{QR_URL}/{charge_id}/confirm", headers=cabeceras)

    assert response.status_code == 409


async def test_no_se_confirma_el_cobro_de_otro_cliente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    creado = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )
    charge_id = creado.json()["id"]
    users = SqlAlchemyUserRepository(session)
    otro = await users.add(build_user("beto@example.com"))
    await session.commit()

    response = await client.post(f"{QR_URL}/{charge_id}/confirm", headers=authorization_for(otro))

    assert response.status_code == 404


async def test_sin_credencial_no_se_llega_a_ninguna_parte(client: AsyncClient) -> None:
    assert (await client.post(QR_URL, json={"appointment_id": 1})).status_code == 401
    assert (await client.get(f"{QR_URL}/1")).status_code == 401
    assert (await client.post(f"{QR_URL}/1/confirm")).status_code == 401


async def test_el_personal_ajusta_el_monto_dentro_del_margen(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Consulta general cuesta S/ 60: dentro de ±5 se acepta."""
    escenario = await montar(session)

    response = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id, "amount": "64.00"},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 201
    assert Decimal(response.json()["amount"]) == Decimal("64.00")


async def test_el_personal_no_se_sale_del_margen_en_una_cita_normal(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id, "amount": "80.00"},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 422


async def test_un_cliente_no_puede_fijar_un_monto(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id, "amount": "60.00"},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_el_personal_ajusta_libremente_en_una_emergencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    """El precio de catálogo de emergencia es S/ 150; acá se cobra bien menos."""
    escenario = await montar_emergencia(session)

    response = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id, "amount": "35.00"},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 201
    assert Decimal(response.json()["amount"]) == Decimal("35.00")


async def test_con_la_simulacion_apagada_confirmar_no_existe(
    client: AsyncClient, session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    escenario = await montar(session)
    cabeceras = authorization_for(escenario.cliente)
    creado = await client.post(
        QR_URL, json={"appointment_id": escenario.cita_id}, headers=cabeceras
    )
    charge_id = creado.json()["id"]
    _apagar_simulacion(monkeypatch)

    response = await client.post(f"{QR_URL}/{charge_id}/confirm", headers=cabeceras)

    assert response.status_code == 404
    estado = await client.get(f"{QR_URL}/{charge_id}", headers=cabeceras)
    assert estado.json()["status"] == "pending"
    assert estado.json()["simulation_available"] is False
    # Ni siquiera sin sesión se distingue de una ruta inexistente.
    assert (await client.post(f"{QR_URL}/{charge_id}/confirm")).status_code == 404


async def test_con_la_simulacion_encendida_el_cobro_la_anuncia(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        QR_URL,
        json={"appointment_id": escenario.cita_id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.json()["simulation_available"] is True


async def test_la_simulacion_no_figura_en_el_esquema(client: AsyncClient) -> None:
    esquema = (await client.get("/api/v1/openapi.json")).json()

    assert "/api/v1/payments/qr-charges/{charge_id}/confirm" not in esquema["paths"]

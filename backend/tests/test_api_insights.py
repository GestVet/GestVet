"""Pruebas del adaptador HTTP del panel de indicadores.

Recorren la aplicación entera contra una base real: es la única forma de
comprobar que las consultas crudas contra tablas ajenas devuelven lo que
dicen devolver.
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
from gestvet.modules.appointments.domain.entities import Appointment, AppointmentStatus
from gestvet.modules.billing.adapters.persistence.repositories import SqlAlchemyPaymentRepository
from gestvet.modules.billing.domain.entities import Payment, PaymentMethod
from gestvet.modules.complaints.adapters.persistence.repositories import (
    SqlAlchemyComplaintRepository,
)
from gestvet.modules.complaints.domain.entities import Complaint
from gestvet.modules.medical_records.adapters.persistence.repositories import (
    SqlAlchemyClinicalEntryRepository,
)
from gestvet.modules.medical_records.domain.entities import ClinicalEntry, EntryKind
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from gestvet.modules.reviews.adapters.persistence.repositories import SqlAlchemyReviewRepository
from gestvet.modules.reviews.domain.entities import Review
from tests.conftest import (
    GENERAL_TYPE_ID,
    SURGERY_TYPE_ID,
    authorization_for,
    build_pet,
    build_user,
)

URL = "/api/v1/insights"
HORA = datetime(2026, 9, 14, 10, 0, tzinfo=UTC)


class Base:
    def __init__(self, admin, cliente, veterinario, pet_id: int) -> None:
        self.admin = admin
        self.cliente = cliente
        self.veterinario = veterinario
        self.pet_id = pet_id


async def _base(session: AsyncSession) -> Base:
    users = SqlAlchemyUserRepository(session)
    admin = await users.add(build_user("jefa@example.com", role=Role.ADMIN))
    cliente = await users.add(build_user("ana@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()

    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=cliente.id or 0))
    await session.commit()
    return Base(admin, cliente, veterinario, mascota.id or 0)


async def _appointment(
    session: AsyncSession, base: Base, scheduled_at: datetime, status: AppointmentStatus
) -> int:
    appointments = SqlAlchemyAppointmentRepository(session)
    cita = await appointments.add(
        Appointment(
            scheduled_at=scheduled_at,
            duration=timedelta(minutes=30),
            client_id=base.cliente.id or 0,
            pet_id=base.pet_id,
            veterinarian_id=base.veterinario.id or 0,
            appointment_type_id=GENERAL_TYPE_ID,
            status=status,
        )
    )
    await session.commit()
    return cita.id or 0


async def test_solo_administracion_ve_los_indicadores(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)

    for path in ("care-reminders", "no-show-risks", "payment-anomalies", "veterinarian-alerts"):
        respuesta = await client.get(f"{URL}/{path}", headers=authorization_for(base.veterinario))
        assert respuesta.status_code == 403

    respuesta = await client.get(f"{URL}/care-reminders")
    assert respuesta.status_code == 401


async def test_recuerda_una_mascota_sin_control_reciente(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)
    entries = SqlAlchemyClinicalEntryRepository(session)
    await entries.add(
        ClinicalEntry(
            pet_id=base.pet_id,
            veterinarian_id=base.veterinario.id or 0,
            kind=EntryKind.CONSULTATION,
            notes="Chequeo de rutina.",
            occurred_at=HORA - timedelta(days=400),
        )
    )
    await session.commit()

    respuesta = await client.get(f"{URL}/care-reminders", headers=authorization_for(base.admin))

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    assert any(item["pet_id"] == base.pet_id and item["reason_label"] for item in items)


async def test_marca_una_cita_proxima_con_riesgo_de_inasistencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)
    await _appointment(session, base, HORA - timedelta(days=10), AppointmentStatus.CONFIRMED)
    await _appointment(session, base, HORA - timedelta(days=5), AppointmentStatus.CONFIRMED)
    proxima_id = await _appointment(
        session, base, datetime.now(UTC) + timedelta(days=1), AppointmentStatus.CONFIRMED
    )

    respuesta = await client.get(f"{URL}/no-show-risks", headers=authorization_for(base.admin))

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    assert any(
        item["appointment_id"] == proxima_id and item["past_incidents"] == 2 for item in items
    )


async def test_detecta_un_pago_fuera_de_lo_tipico(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)
    cita_id = await _appointment(session, base, HORA, AppointmentStatus.COMPLETED)
    payments = SqlAlchemyPaymentRepository(session)
    for monto in (Decimal("50"), Decimal("52"), Decimal("48")):
        await payments.add(
            Payment(
                appointment_id=cita_id,
                client_id=base.cliente.id or 0,
                amount=monto,
                method=PaymentMethod.CASH,
                registered_by=base.veterinario.id or 0,
            )
        )
    await payments.add(
        Payment(
            appointment_id=cita_id,
            client_id=base.cliente.id or 0,
            amount=Decimal("300"),
            method=PaymentMethod.CASH,
            registered_by=base.veterinario.id or 0,
        )
    )
    await session.commit()

    respuesta = await client.get(f"{URL}/payment-anomalies", headers=authorization_for(base.admin))

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    atipico = next(item for item in items if item["amount"] == "300.00")
    assert atipico["client_name"] == f"{base.cliente.first_name} {base.cliente.last_name}"
    assert atipico["pet_name"] == "Rocco"


async def test_alerta_un_veterinario_con_reclamos_recientes(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)
    cita_id = await _appointment(session, base, HORA, AppointmentStatus.COMPLETED)
    complaints = SqlAlchemyComplaintRepository(session)
    for _ in range(2):
        await complaints.add(
            Complaint(
                client_id=base.cliente.id or 0,
                veterinarian_id=base.veterinario.id or 0,
                appointment_id=cita_id,
                description="No revisó bien a mi mascota.",
            )
        )
    await session.commit()

    respuesta = await client.get(
        f"{URL}/veterinarian-alerts", headers=authorization_for(base.admin)
    )

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    assert any(
        item["veterinarian_id"] == base.veterinario.id and item["complaint_count"] == 2
        for item in items
    )


async def test_administracion_ve_todas_las_mascotas_veterinario_solo_las_que_atendio(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)
    users = SqlAlchemyUserRepository(session)
    otro_cliente = await users.add(build_user("otro@example.com"))
    otro_veterinario = await users.add(build_user("otrovet@example.com", role=Role.VETERINARIAN))
    await session.flush()

    pets = SqlAlchemyPetRepository(session)
    otra_mascota = await pets.add(build_pet(owner_id=otro_cliente.id or 0, name="Michi"))
    await session.commit()

    entries = SqlAlchemyClinicalEntryRepository(session)
    await entries.add(
        ClinicalEntry(
            pet_id=base.pet_id,
            veterinarian_id=base.veterinario.id or 0,
            kind=EntryKind.CONSULTATION,
            notes="Consulta inicial.",
            occurred_at=HORA,
        )
    )
    await session.commit()

    respuesta_admin = await client.get(
        f"{URL}/pets-overview", headers=authorization_for(base.admin)
    )
    assert respuesta_admin.status_code == 200
    ids_admin = {item["pet_id"] for item in respuesta_admin.json()["items"]}
    assert ids_admin == {base.pet_id, otra_mascota.id}

    respuesta_vet = await client.get(
        f"{URL}/pets-overview", headers=authorization_for(base.veterinario)
    )
    assert respuesta_vet.status_code == 200
    items_vet = respuesta_vet.json()["items"]
    assert {item["pet_id"] for item in items_vet} == {base.pet_id}
    assert items_vet[0]["vaccination_status"] == "no_vaccines"

    respuesta_otro_vet = await client.get(
        f"{URL}/pets-overview", headers=authorization_for(otro_veterinario)
    )
    assert respuesta_otro_vet.status_code == 200
    assert respuesta_otro_vet.json()["items"] == []

    respuesta_cliente = await client.get(
        f"{URL}/pets-overview", headers=authorization_for(base.cliente)
    )
    assert respuesta_cliente.status_code == 403


async def test_solo_administracion_ve_servicios_mas_consumidos(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)

    respuesta = await client.get(
        f"{URL}/service-consumption", headers=authorization_for(base.veterinario)
    )
    assert respuesta.status_code == 403

    respuesta = await client.get(f"{URL}/service-consumption")
    assert respuesta.status_code == 401


async def test_cuenta_citas_por_servicio_sin_exponer_clientes(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)
    await _appointment(session, base, HORA, AppointmentStatus.COMPLETED)
    await _appointment(session, base, HORA + timedelta(days=1), AppointmentStatus.CANCELLED)

    respuesta = await client.get(
        f"{URL}/service-consumption", headers=authorization_for(base.admin)
    )
    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    general = next(item for item in items if item["appointment_type_id"] == GENERAL_TYPE_ID)
    assert general["appointment_count"] == 2
    assert general["estimated_revenue"] == "120.00"
    assert "client_name" not in general
    assert "owner_name" not in general

    solo_completadas = await client.get(
        f"{URL}/service-consumption",
        params={"status": "completed"},
        headers=authorization_for(base.admin),
    )
    general_filtrado = next(
        item
        for item in solo_completadas.json()["items"]
        if item["appointment_type_id"] == GENERAL_TYPE_ID
    )
    assert general_filtrado["appointment_count"] == 1


async def test_un_servicio_sin_citas_en_el_rango_aparece_en_cero(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)
    await _appointment(session, base, HORA, AppointmentStatus.COMPLETED)

    respuesta = await client.get(
        f"{URL}/service-consumption", headers=authorization_for(base.admin)
    )

    items = respuesta.json()["items"]
    cirugia = next(item for item in items if item["appointment_type_id"] == SURGERY_TYPE_ID)
    assert cirugia["appointment_count"] == 0


async def test_descarga_el_pdf_de_servicios_mas_consumidos(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)

    respuesta = await client.get(
        f"{URL}/service-consumption.pdf", headers=authorization_for(base.admin)
    )

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/pdf"


async def test_un_veterinario_con_buena_reputacion_no_genera_alerta(
    client: AsyncClient, session: AsyncSession
) -> None:
    base = await _base(session)
    reviews = SqlAlchemyReviewRepository(session)
    await reviews.add(
        Review(
            veterinarian_id=base.veterinario.id or 0,
            client_id=base.cliente.id or 0,
            rating=5,
            comment="Excelente atención.",
        )
    )
    await session.commit()

    respuesta = await client.get(
        f"{URL}/veterinarian-alerts", headers=authorization_for(base.admin)
    )

    assert respuesta.status_code == 200
    ids = [item["veterinarian_id"] for item in respuesta.json()["items"]]
    assert base.veterinario.id not in ids

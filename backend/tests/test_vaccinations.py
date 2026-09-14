"""El carnet de vacunas: reglas de fechas y el recorrido HTTP completo."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.clinic_time import clinic_date
from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.medical_records.domain.exceptions import InvalidVaccination
from gestvet.modules.medical_records.domain.vaccination import (
    PRIMARY_SERIES_DAYS,
    Vaccination,
    VaccinationStatus,
    VaccineCode,
    status_on,
    suggested_interval_days,
    summarize,
)
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import authorization_for, build_pet, build_user

URL = "/api/v1/medical-records/vaccinations"
HOY = clinic_date(datetime.now(UTC))


def _vacuna(
    code: VaccineCode, applied_on: date, next_due_on: date | None, **extra: str
) -> Vaccination:
    return Vaccination(
        pet_id=1,
        veterinarian_id=1,
        vaccine=code,
        applied_on=applied_on,
        next_due_on=next_due_on,
        **extra,
    )


def test_un_cachorro_recibe_la_serie_cada_tres_semanas_y_un_adulto_cada_ano() -> None:
    cachorro = HOY - timedelta(days=60)
    adulto = HOY - timedelta(days=800)

    assert (
        suggested_interval_days(VaccineCode.DOG_MULTIVALENT, applied_on=HOY, birth_date=cachorro)
        == PRIMARY_SERIES_DAYS
    )
    assert (
        suggested_interval_days(VaccineCode.DOG_MULTIVALENT, applied_on=HOY, birth_date=adulto)
        == 365
    )
    # La antirrábica no va en serie: es anual a cualquier edad.
    assert suggested_interval_days(VaccineCode.RABIES, applied_on=HOY, birth_date=cachorro) == 365
    assert suggested_interval_days(VaccineCode.OTHER, applied_on=HOY, birth_date=adulto) is None


@pytest.mark.parametrize(
    ("proxima", "estado"),
    [
        (None, VaccinationStatus.NO_BOOSTER),
        (HOY - timedelta(days=1), VaccinationStatus.OVERDUE),
        (HOY + timedelta(days=10), VaccinationStatus.DUE_SOON),
        (HOY + timedelta(days=200), VaccinationStatus.UP_TO_DATE),
    ],
)
def test_el_estado_sale_de_la_proxima_dosis(
    proxima: date | None, estado: VaccinationStatus
) -> None:
    assert status_on(proxima, HOY) is estado


def test_el_resumen_usa_la_ultima_aplicacion_y_pone_lo_vencido_primero() -> None:
    vieja = _vacuna(VaccineCode.RABIES, HOY - timedelta(days=700), HOY - timedelta(days=335))
    nueva = _vacuna(VaccineCode.RABIES, HOY - timedelta(days=30), HOY + timedelta(days=335))
    vencida = _vacuna(VaccineCode.DEWORMING, HOY - timedelta(days=120), HOY - timedelta(days=30))

    resumen = summarize([vieja, nueva, vencida], HOY)

    assert [(item.vaccine, item.status) for item in resumen] == [
        (VaccineCode.DEWORMING, VaccinationStatus.OVERDUE),
        (VaccineCode.RABIES, VaccinationStatus.UP_TO_DATE),
    ]


@pytest.mark.parametrize(
    ("aplicada", "proxima", "producto"),
    [
        (HOY + timedelta(days=1), None, ""),
        (HOY, HOY, ""),
    ],
)
def test_fechas_imposibles_se_rechazan(aplicada: date, proxima: date | None, producto: str) -> None:
    with pytest.raises(InvalidVaccination):
        _vacuna(VaccineCode.RABIES, aplicada, proxima, product_name=producto)


def test_otra_vacuna_exige_el_nombre_del_producto() -> None:
    with pytest.raises(InvalidVaccination):
        _vacuna(VaccineCode.OTHER, HOY, None)


class Escenario:
    def __init__(self, cliente, ajeno, veterinario, mascota) -> None:
        self.cliente = cliente
        self.ajeno = ajeno
        self.veterinario = veterinario
        self.mascota = mascota


async def montar(session: AsyncSession, species: str = "Perro") -> Escenario:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    ajeno = await users.add(build_user("otro@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()
    mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=cliente.id or 0, species=species, breed="Sin especificar")
    )
    await session.commit()
    return Escenario(cliente, ajeno, veterinario, mascota)


async def test_el_veterinario_registra_y_el_dueno_ve_el_carnet(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    proxima = HOY + timedelta(days=365)

    creada = await client.post(
        URL,
        json={
            "pet_id": escenario.mascota.id,
            "vaccine": "rabies",
            "applied_on": HOY.isoformat(),
            "next_due_on": proxima.isoformat(),
            "product_name": "Nobivac Rabies",
            "batch": "A123B45",
        },
        headers=authorization_for(escenario.veterinario),
    )
    carnet = await client.get(
        URL, params={"pet_id": escenario.mascota.id}, headers=authorization_for(escenario.cliente)
    )

    assert creada.status_code == 201
    assert creada.json()["vaccine_label"] == "Antirrábica"
    assert carnet.status_code == 200
    body = carnet.json()
    assert [item["batch"] for item in body["items"]] == ["A123B45"]
    assert body["summary"][0]["status"] == "up_to_date"
    assert body["summary"][0]["status_label"] == "Al día"


async def test_otro_cliente_no_ve_el_carnet(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.get(
        URL, params={"pet_id": escenario.mascota.id}, headers=authorization_for(escenario.ajeno)
    )

    assert response.status_code == 404


async def test_el_dueno_no_registra_vacunas(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={"pet_id": escenario.mascota.id, "vaccine": "rabies", "applied_on": HOY.isoformat()},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_una_vacuna_de_gato_no_se_registra_a_un_perro(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        URL,
        json={
            "pet_id": escenario.mascota.id,
            "vaccine": "cat_triple",
            "applied_on": HOY.isoformat(),
        },
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 422


async def test_las_opciones_dependen_de_la_especie(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session, species="Gato")

    response = await client.get(
        f"{URL}/options",
        params={"pet_id": escenario.mascota.id},
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 200
    vacunas = {item["vaccine"] for item in response.json()["items"]}
    assert "cat_triple" in vacunas
    assert "dog_multivalent" not in vacunas

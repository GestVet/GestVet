"""El carnet de vacunas en PDF y su verificación pública por QR."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.core.signed_links import SignedLinks
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.medical_records.adapters.api.dependencies import get_card_links
from gestvet.modules.medical_records.adapters.reports.vaccination_card_pdf import (
    ReportLabVaccinationCard,
)
from gestvet.modules.medical_records.domain.vaccination import Vaccination, VaccineCode, summarize
from gestvet.modules.medical_records.ports.pet_directory import PetSummary
from gestvet.modules.medical_records.ports.vaccination_card_report import VaccinationCardDocument
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import authorization_for, build_pet, build_user

AHORA = datetime(2026, 9, 14, 15, tzinfo=UTC)
CARD_URL = "/api/v1/medical-records/vaccinations/card.pdf"
PUBLIC_URL = "/api/v1/public/vaccination-cards"


def test_un_enlace_firmado_se_lee_y_no_se_puede_alterar() -> None:
    links = SignedLinks("secreto-de-prueba-con-largo-suficiente", purpose="carnet")
    token = links.sign(42, AHORA + timedelta(days=1))

    referencia = links.read(token, AHORA)
    assert referencia is not None
    assert referencia.subject_id == 42

    payload, _, firma = token.partition(".")
    otro = SignedLinks("secreto-de-prueba-con-largo-suficiente", purpose="carnet").sign(
        43, AHORA + timedelta(days=1)
    )
    assert links.read(f"{otro.partition('.')[0]}.{firma}", AHORA) is None
    assert links.read(f"{payload}.firma-inventada", AHORA) is None
    assert links.read("basura", AHORA) is None
    assert links.read("ñ.ñ", AHORA) is None


def test_un_enlace_vencido_o_de_otro_proposito_no_vale() -> None:
    links = SignedLinks("secreto-de-prueba-con-largo-suficiente", purpose="carnet")
    token = links.sign(42, AHORA + timedelta(days=1))

    assert links.read(token, AHORA + timedelta(days=2)) is None
    otro_uso = SignedLinks("secreto-de-prueba-con-largo-suficiente", purpose="otra-cosa")
    assert otro_uso.read(token, AHORA) is None


def test_el_pdf_se_genera_con_y_sin_vacunas() -> None:
    mascota = PetSummary(
        name="Rocco",
        species="Perro",
        breed="Mestizo",
        owner_name="Ana Quispe",
        sex_label="Macho",
        color="Negro",
        microchip_number="604000000123456",
        temperament="",
        weight_kg=None,
        height_cm=None,
        is_sterilized=None,
        allergies="",
        birth_date=date(2021, 3, 14),
    )
    vacuna = Vaccination(
        pet_id=1,
        veterinarian_id=1,
        vaccine=VaccineCode.RABIES,
        applied_on=date(2026, 9, 1),
        next_due_on=date(2027, 9, 1),
        product_name="Nobivac Rabies",
        batch="A123B45",
    )
    renderer = ReportLabVaccinationCard()

    for items in ([vacuna], []):
        pdf = renderer.render(
            VaccinationCardDocument(
                pet=mascota,
                summary=summarize(items, date(2026, 9, 14)),
                items=items,
                verification_url="http://localhost:5173/carnet/abc.def",
                issued_on=date(2026, 9, 14),
                valid_until=date(2027, 9, 14),
            )
        )
        assert pdf.startswith(b"%PDF")


async def _escenario(session: AsyncSession):
    users = SqlAlchemyUserRepository(session)
    dueno = await users.add(build_user("ana@example.com", last_name="Quispe"))
    ajeno = await users.add(build_user("otro@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()
    mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=dueno.id or 0, name="Rocco")
    )
    await session.commit()
    return dueno, ajeno, veterinario, mascota


async def test_el_dueno_baja_el_carnet_y_otro_cliente_no(
    client: AsyncClient, session: AsyncSession
) -> None:
    dueno, ajeno, _, mascota = await _escenario(session)

    propio = await client.get(
        CARD_URL, params={"pet_id": mascota.id}, headers=authorization_for(dueno)
    )
    de_otro = await client.get(
        CARD_URL, params={"pet_id": mascota.id}, headers=authorization_for(ajeno)
    )

    assert propio.status_code == 200
    assert propio.headers["content-type"] == "application/pdf"
    assert "carnet-de-vacunas-rocco.pdf" in propio.headers["content-disposition"]
    assert propio.content.startswith(b"%PDF")
    assert de_otro.status_code == 404


async def test_el_qr_muestra_las_vacunas_sin_datos_del_dueno(
    client: AsyncClient, session: AsyncSession
) -> None:
    _, _, veterinario, mascota = await _escenario(session)
    hoy = datetime.now(UTC).date()
    await client.post(
        "/api/v1/medical-records/vaccinations",
        json={
            "pet_id": mascota.id,
            "vaccine": "rabies",
            "applied_on": (hoy - timedelta(days=1)).isoformat(),
            "next_due_on": (hoy + timedelta(days=364)).isoformat(),
        },
        headers=authorization_for(veterinario),
    )
    token = get_card_links().sign(mascota.id or 0, datetime.now(UTC) + timedelta(days=30))

    response = await client.get(f"{PUBLIC_URL}/{token}")

    assert response.status_code == 200
    body = response.json()
    assert body["pet_name"] == "Rocco"
    assert [item["label"] for item in body["summary"]] == ["Antirrábica"]
    assert "Quispe" not in response.text
    assert "ana@example.com" not in response.text


async def test_un_qr_alterado_responde_404(client: AsyncClient, session: AsyncSession) -> None:
    _, _, _, mascota = await _escenario(session)
    token = get_card_links().sign(mascota.id or 0, datetime.now(UTC) + timedelta(days=30))

    response = await client.get(f"{PUBLIC_URL}/{token[:-3]}abc")

    assert response.status_code == 404

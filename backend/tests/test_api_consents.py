"""Pruebas del adaptador HTTP de consentimientos y de su uso al abrir emergencias."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.domain.entities import User
from gestvet.modules.availability.adapters.persistence.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityRepository,
)
from gestvet.modules.availability.domain.entities import AvailabilitySlot, ShiftKind
from gestvet.modules.consents.adapters.persistence.models import ConsentRow, ConsentTemplateRow
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from gestvet.modules.pets.domain.entities import Pet
from tests.conftest import (
    EMERGENCY_RISK_TEMPLATE,
    EMERGENCY_RISK_TEMPLATE_ID,
    authorization_for,
    build_pet,
    build_user,
)

URL = "/api/v1/consents"
EMERGENCIAS = "/api/v1/appointments/emergency"


class Clinica:
    def __init__(
        self, cliente: User, mascota: Pet, otra_mascota: Pet, veterinario: User, intruso: User
    ) -> None:
        self.cliente = cliente
        self.mascota = mascota
        self.otra_mascota = otra_mascota
        self.veterinario = veterinario
        self.intruso = intruso


async def montar(session: AsyncSession) -> Clinica:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    intruso = await users.add(build_user("beto@example.com", first_name="Beto"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()
    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=cliente.id or 0))
    otra = await pets.add(build_pet(owner_id=cliente.id or 0, name="Luna"))
    ahora = datetime.now(UTC)
    await SqlAlchemyAvailabilityRepository(session).add(
        AvailabilitySlot(
            veterinarian_id=veterinario.id or 0,
            starts_at=ahora - timedelta(hours=1),
            ends_at=ahora + timedelta(hours=11),
            kind=ShiftKind.ON_CALL,
        )
    )
    await session.commit()
    return Clinica(cliente, mascota, otra, veterinario, intruso)


def firma(pet_id: int | None, **extra: object) -> dict[str, object]:
    cuerpo: dict[str, object] = {
        "pet_id": pet_id,
        "template_id": EMERGENCY_RISK_TEMPLATE_ID,
        "signer_name": "Ana Quispe",
        "accepted": True,
    }
    cuerpo.update(extra)
    return cuerpo


async def firmar(client: AsyncClient, clinica: Clinica, pet_id: int | None = None) -> int:
    response = await client.post(
        f"{URL}/emergency-risk",
        json=firma(pet_id or clinica.mascota.id),
        headers=authorization_for(clinica.cliente),
    )
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


async def test_el_texto_vigente_trae_su_version(client: AsyncClient, session: AsyncSession) -> None:
    clinica = await montar(session)

    response = await client.get(
        f"{URL}/templates/current",
        params={"kind": "emergency_risk"},
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == EMERGENCY_RISK_TEMPLATE_ID
    assert body["version"] == 1
    assert body["body"] == EMERGENCY_RISK_TEMPLATE["body"]
    assert body["text"].startswith(str(EMERGENCY_RISK_TEMPLATE["title"]))


async def test_el_cliente_firma_en_linea_y_queda_la_constancia(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.post(
        f"{URL}/emergency-risk",
        json=firma(clinica.mascota.id, signer_name="  Ana   Quispe "),
        headers={**authorization_for(clinica.cliente), "User-Agent": "Navegador de prueba"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "accepted"
    assert body["channel"] == "online"
    assert body["signer_name"] == "Ana Quispe"
    assert body["signer_user_id"] == clinica.cliente.id
    assert body["client_id"] == clinica.cliente.id
    assert len(body["text_sha256"]) == 64
    assert "ip" not in body
    guardado = await session.get(ConsentRow, body["id"])
    assert guardado is not None
    assert guardado.user_agent == "Navegador de prueba"


async def test_sin_la_casilla_no_hay_consentimiento(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.post(
        f"{URL}/emergency-risk",
        json=firma(clinica.mascota.id, accepted=False),
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 422


async def test_un_nombre_de_una_palabra_no_es_una_firma(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.post(
        f"{URL}/emergency-risk",
        json=firma(clinica.mascota.id, signer_name="Ana"),
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 422
    assert "nombre completo" in response.json()["detail"]


async def test_no_se_firma_por_la_mascota_de_otro(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.post(
        f"{URL}/emergency-risk",
        json=firma(clinica.mascota.id),
        headers=authorization_for(clinica.intruso),
    )

    assert response.status_code == 404


async def test_firmar_un_texto_reemplazado_pide_releerlo(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    session.add(
        ConsentTemplateRow(
            kind="emergency_risk", version=2, title="Riesgo", body="Texto corregido."
        )
    )
    await session.commit()

    response = await client.post(
        f"{URL}/emergency-risk",
        json=firma(clinica.mascota.id),
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 409


async def test_un_consentimiento_ajeno_responde_como_inexistente(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    consent_id = await firmar(client, clinica)

    propio = await client.get(f"{URL}/{consent_id}", headers=authorization_for(clinica.cliente))
    ajeno = await client.get(f"{URL}/{consent_id}", headers=authorization_for(clinica.intruso))
    del_personal = await client.get(
        f"{URL}/{consent_id}", headers=authorization_for(clinica.veterinario)
    )

    assert propio.status_code == 200
    assert ajeno.status_code == 404
    assert del_personal.status_code == 200
    assert del_personal.json()["signer_name"] == "Ana Quispe"


async def test_el_personal_registra_la_firma_presencial(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.post(
        f"{URL}/emergency-risk/in-person",
        json=firma(clinica.mascota.id, client_id=clinica.cliente.id, signer_name="Rosa Quispe"),
        headers=authorization_for(clinica.veterinario),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["channel"] == "in_person"
    assert body["witness_id"] == clinica.veterinario.id
    assert body["signer_user_id"] is None
    assert body["client_id"] == clinica.cliente.id


async def test_un_cliente_no_registra_firmas_presenciales(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.post(
        f"{URL}/emergency-risk/in-person",
        json=firma(clinica.mascota.id, client_id=clinica.cliente.id),
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 403


async def test_en_el_mostrador_la_mascota_tiene_que_ser_del_cliente(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.post(
        f"{URL}/emergency-risk/in-person",
        json=firma(clinica.mascota.id, client_id=clinica.intruso.id),
        headers=authorization_for(clinica.veterinario),
    )

    assert response.status_code == 404


async def test_la_emergencia_guarda_la_firma_que_la_habilito(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    consent_id = await firmar(client, clinica)

    response = await client.post(
        EMERGENCIAS,
        json={"pet_id": clinica.mascota.id, "risk_consent_id": consent_id},
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 201
    assert response.json()["risk_consent_id"] == consent_id


async def test_sin_firma_no_se_abre_la_emergencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)

    response = await client.post(
        EMERGENCIAS,
        json={"pet_id": clinica.mascota.id},
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 422


async def test_una_firma_vencida_no_abre_la_emergencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    consent_id = await firmar(client, clinica)
    await session.execute(
        update(ConsentRow)
        .where(ConsentRow.id == consent_id)
        .values(decided_at=datetime.now(UTC) - timedelta(minutes=31))
    )
    await session.commit()

    response = await client.post(
        EMERGENCIAS,
        json={"pet_id": clinica.mascota.id, "risk_consent_id": consent_id},
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 422
    assert "30 minutos" in response.json()["detail"]


async def test_una_firma_de_otra_mascota_no_abre_la_emergencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    consent_id = await firmar(client, clinica, clinica.otra_mascota.id)

    response = await client.post(
        EMERGENCIAS,
        json={"pet_id": clinica.mascota.id, "risk_consent_id": consent_id},
        headers=authorization_for(clinica.cliente),
    )

    assert response.status_code == 422
    assert "otra mascota" in response.json()["detail"]


async def test_una_firma_no_abre_dos_emergencias(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    consent_id = await firmar(client, clinica)
    cuerpo = {"pet_id": clinica.mascota.id, "risk_consent_id": consent_id}

    primera = await client.post(
        EMERGENCIAS, json=cuerpo, headers=authorization_for(clinica.cliente)
    )
    segunda = await client.post(
        EMERGENCIAS, json=cuerpo, headers=authorization_for(clinica.cliente)
    )

    assert primera.status_code == 201
    assert segunda.status_code == 422
    assert "ya se usó" in segunda.json()["detail"]


async def test_la_firma_de_otro_cliente_no_abre_la_emergencia(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    consent_id = await firmar(client, clinica)
    mascota_del_intruso = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=clinica.intruso.id or 0, name="Toby")
    )
    await session.commit()

    response = await client.post(
        EMERGENCIAS,
        json={"pet_id": mascota_del_intruso.id, "risk_consent_id": consent_id},
        headers=authorization_for(clinica.intruso),
    )

    assert response.status_code == 422
    assert "No encontramos" in response.json()["detail"]


async def test_el_mostrador_abre_la_emergencia_con_la_firma_presencial(
    client: AsyncClient, session: AsyncSession
) -> None:
    clinica = await montar(session)
    presencial = await client.post(
        f"{URL}/emergency-risk/in-person",
        json=firma(clinica.mascota.id, client_id=clinica.cliente.id),
        headers=authorization_for(clinica.veterinario),
    )
    consent_id = presencial.json()["id"]

    response = await client.post(
        f"{EMERGENCIAS}/walk-in",
        json={
            "client_id": clinica.cliente.id,
            "pet_id": clinica.mascota.id,
            "risk_consent_id": consent_id,
            "description": "Atropellado",
        },
        headers=authorization_for(clinica.veterinario),
    )

    assert response.status_code == 201
    assert response.json()["risk_consent_id"] == consent_id

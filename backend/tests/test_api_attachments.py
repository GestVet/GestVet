"""Pruebas del adaptador HTTP de los adjuntos de la historia clínica."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.medical_records.adapters.persistence.repositories import (
    SqlAlchemyClinicalEntryRepository,
)
from gestvet.modules.medical_records.domain.entities import ClinicalEntry, EntryKind
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import authorization_for, build_pet, build_user

URL = "/api/v1/medical-records"


class Escenario:
    def __init__(self, cliente, veterinario, pet_id: int, entrada_id: int) -> None:
        self.cliente = cliente
        self.veterinario = veterinario
        self.pet_id = pet_id
        self.entrada_id = entrada_id


async def montar(session: AsyncSession) -> Escenario:
    users = SqlAlchemyUserRepository(session)
    cliente = await users.add(build_user("ana@example.com"))
    veterinario = await users.add(build_user("vet@example.com", role=Role.VETERINARIAN))
    await session.flush()

    pets = SqlAlchemyPetRepository(session)
    mascota = await pets.add(build_pet(owner_id=cliente.id or 0))

    entries = SqlAlchemyClinicalEntryRepository(session)
    entrada = await entries.add(
        ClinicalEntry(
            pet_id=mascota.id or 0,
            veterinarian_id=veterinario.id or 0,
            kind=EntryKind.CONSULTATION,
            notes="Buen estado general.",
        )
    )
    await session.commit()
    return Escenario(cliente, veterinario, mascota.id or 0, entrada.id or 0)


def _archivo(nombre: str = "radiografia.jpg", tipo: str = "image/jpeg") -> dict:
    return {"file": (nombre, b"contenido-de-prueba", tipo)}


async def test_un_veterinario_adjunta_un_archivo(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        f"{URL}/{escenario.entrada_id}/attachments",
        files=_archivo(),
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["clinical_entry_id"] == escenario.entrada_id
    assert body["filename"] == "radiografia.jpg"
    assert body["content_type"] == "image/jpeg"
    assert body["size_bytes"] == len(b"contenido-de-prueba")
    assert body["url"] != ""


async def test_un_cliente_no_puede_adjuntar_un_archivo(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        f"{URL}/{escenario.entrada_id}/attachments",
        files=_archivo(),
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_no_se_puede_adjuntar_a_una_entrada_inexistente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        f"{URL}/999/attachments",
        files=_archivo(),
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 404


async def test_un_tipo_no_permitido_es_rechazado(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.post(
        f"{URL}/{escenario.entrada_id}/attachments",
        files=_archivo("virus.exe", "application/x-msdownload"),
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 422


async def test_el_adjunto_aparece_en_la_historia_clinica(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    await client.post(
        f"{URL}/{escenario.entrada_id}/attachments",
        files=_archivo(),
        headers=authorization_for(escenario.veterinario),
    )

    response = await client.get(
        URL,
        params={"pet_id": escenario.pet_id},
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"][0]["attachments"]) == 1
    assert body["items"][0]["attachments"][0]["filename"] == "radiografia.jpg"


async def test_un_veterinario_quita_un_adjunto(client: AsyncClient, session: AsyncSession) -> None:
    escenario = await montar(session)
    subida = await client.post(
        f"{URL}/{escenario.entrada_id}/attachments",
        files=_archivo(),
        headers=authorization_for(escenario.veterinario),
    )
    adjunto_id = subida.json()["id"]

    response = await client.delete(
        f"{URL}/attachments/{adjunto_id}",
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 204

    historia = await client.get(
        URL,
        params={"pet_id": escenario.pet_id},
        headers=authorization_for(escenario.veterinario),
    )
    assert historia.json()["items"][0]["attachments"] == []


async def test_no_se_puede_quitar_un_adjunto_inexistente(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)

    response = await client.delete(
        f"{URL}/attachments/999",
        headers=authorization_for(escenario.veterinario),
    )

    assert response.status_code == 404


async def test_un_cliente_no_puede_quitar_un_adjunto(
    client: AsyncClient, session: AsyncSession
) -> None:
    escenario = await montar(session)
    subida = await client.post(
        f"{URL}/{escenario.entrada_id}/attachments",
        files=_archivo(),
        headers=authorization_for(escenario.veterinario),
    )
    adjunto_id = subida.json()["id"]

    response = await client.delete(
        f"{URL}/attachments/{adjunto_id}",
        headers=authorization_for(escenario.cliente),
    )

    assert response.status_code == 403


async def test_sin_credencial_no_se_llega_a_ninguna_parte(client: AsyncClient) -> None:
    assert (await client.post(f"{URL}/1/attachments", files=_archivo())).status_code == 401
    assert (await client.delete(f"{URL}/attachments/1")).status_code == 401

"""El asistente de IA de la historia clínica, con un modelo falso.

Ninguna prueba llama a OpenRouter: `llm` en `conftest` reemplaza al cliente real.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.core.llm import LlmUnavailable
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.medical_records.domain.clinical_summary import (
    MAX_ITEMS,
    summary_from_response,
)
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from tests.conftest import FakeLlmClient, authorization_for, build_pet, build_user

URL = "/api/v1/medical-records/assistant/summary"


def test_la_respuesta_del_modelo_se_valida_y_se_recorta() -> None:
    resumen = summary_from_response(
        {
            "resumen": "  Perro sano con control al día.  ",
            "alertas": ["Alergia a la penicilina", 3, "", *[f"extra {i}" for i in range(10)]],
            "pendientes": "no es una lista",
        },
        "modelo",
    )

    assert resumen.summary == "Perro sano con control al día."
    assert resumen.alerts[0] == "Alergia a la penicilina"
    assert len(resumen.alerts) == MAX_ITEMS
    assert resumen.follow_ups == ()


def test_una_respuesta_sin_resumen_es_un_fallo_del_asistente() -> None:
    with pytest.raises(LlmUnavailable):
        summary_from_response({"alertas": []}, "modelo")


async def _escenario(session: AsyncSession):
    users = SqlAlchemyUserRepository(session)
    dueno = await users.add(build_user("ana@example.com", first_name="Ana", last_name="Quispe"))
    veterinario = await users.add(
        build_user("vet@example.com", role=Role.VETERINARIAN, first_name="Luis", last_name="Rojas")
    )
    await session.flush()
    mascota = await SqlAlchemyPetRepository(session).add(
        build_pet(owner_id=dueno.id or 0, name="Rocco", birth_date=date(2021, 3, 14))
    )
    await session.commit()
    return dueno, veterinario, mascota


async def test_el_veterinario_recibe_un_resumen_sin_datos_del_dueno(
    client: AsyncClient, session: AsyncSession, llm: FakeLlmClient
) -> None:
    _, veterinario, mascota = await _escenario(session)
    await client.post(
        "/api/v1/medical-records",
        json={
            "pet_id": mascota.id,
            "kind": "consultation",
            "notes": "Otitis leve en oído derecho.",
            "diagnosis": "Otitis externa",
            "occurred_at": datetime(2026, 5, 2, 15, tzinfo=UTC).isoformat(),
        },
        headers=authorization_for(veterinario),
    )

    response = await client.post(
        URL, json={"pet_id": mascota.id}, headers=authorization_for(veterinario)
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "Mascota sana, sin novedades."
    contexto = llm.requests[-1].user
    assert "Rocco" in contexto
    assert "Otitis externa" in contexto
    assert "Quispe" not in contexto
    assert "ana@example.com" not in contexto


async def test_sin_asistente_configurado_responde_503(
    client: AsyncClient, session: AsyncSession, llm: FakeLlmClient
) -> None:
    _, veterinario, mascota = await _escenario(session)
    llm.response = None

    response = await client.post(
        URL, json={"pet_id": mascota.id}, headers=authorization_for(veterinario)
    )

    assert response.status_code == 503


async def test_el_dueno_no_pide_resumenes(client: AsyncClient, session: AsyncSession) -> None:
    dueno, _, mascota = await _escenario(session)

    response = await client.post(URL, json={"pet_id": mascota.id}, headers=authorization_for(dueno))

    assert response.status_code == 403

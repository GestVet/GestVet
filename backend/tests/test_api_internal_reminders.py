"""Pruebas del endpoint interno para el cron de recordatorios."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from gestvet.core.config import get_settings

ENDPOINT = "/api/v1/internal/reminders/run"
TEST_TOKEN = "mi-token-secreto-de-cron"


async def test_cron_reminders_sin_configurar_responde_404(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REMINDERS_CRON_TOKEN", "")
    get_settings.cache_clear()

    response = await client.post(ENDPOINT)
    assert response.status_code == 404
    assert response.json()["detail"] == "Endpoint no habilitado."


async def test_cron_reminders_sin_token_responde_401(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REMINDERS_CRON_TOKEN", TEST_TOKEN)
    get_settings.cache_clear()

    response = await client.post(ENDPOINT)
    assert response.status_code == 401
    assert response.json()["detail"] == "Token de recordatorios inválido."


async def test_cron_reminders_token_malo_responde_401(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REMINDERS_CRON_TOKEN", TEST_TOKEN)
    get_settings.cache_clear()

    response = await client.post(ENDPOINT, headers={"X-Reminders-Token": "token-equivocado"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token de recordatorios inválido."


async def test_cron_reminders_token_bueno_responde_200(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REMINDERS_CRON_TOKEN", TEST_TOKEN)
    get_settings.cache_clear()

    response = await client.post(ENDPOINT, headers={"X-Reminders-Token": TEST_TOKEN})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "jobs" in payload
    assert payload["jobs"]["_send_due_reminders"] == "ok"
    assert payload["jobs"]["_send_due_vaccine_reminders"] == "ok"


async def test_cron_reminders_token_bueno_via_bearer_responde_200(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REMINDERS_CRON_TOKEN", TEST_TOKEN)
    get_settings.cache_clear()

    response = await client.post(ENDPOINT, headers={"Authorization": f"Bearer {TEST_TOKEN}"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

"""Avisos en tiempo real: a quién llegan y cuándo salen."""

from __future__ import annotations

import asyncio

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Principal, Role
from gestvet.core.realtime import APPOINTMENTS_TOPIC, RealtimeEvent
from gestvet.core.realtime_broker import (
    LocalBroker,
    SessionEventPublisher,
    decode_event,
    encode_event,
)
from tests.conftest import authorization_for
from tests.test_api_appointments import URL, montar

EVENTS_URL = "/api/v1/events"


def _event() -> RealtimeEvent:
    return RealtimeEvent(
        topic=APPOINTMENTS_TOPIC,
        user_ids=frozenset({3, 7}),
        roles=frozenset({Role.ADMIN}),
        reference_id=42,
    )


def test_event_reaches_participants_and_roles_only() -> None:
    event = _event()

    assert event.is_for(Principal(user_id=3, role=Role.CLIENT, is_active=True))
    assert event.is_for(Principal(user_id=99, role=Role.ADMIN, is_active=True))
    assert not event.is_for(Principal(user_id=99, role=Role.VETERINARIAN, is_active=True))


def test_event_survives_the_trip_through_postgres() -> None:
    assert decode_event(encode_event(_event())) == _event()


async def test_event_is_released_only_after_commit(session: AsyncSession) -> None:
    broker = LocalBroker()
    publisher = SessionEventPublisher(session, broker)

    async with broker.subscribe() as queue:
        publisher.publish(_event())
        assert queue.empty()

        await session.commit()

        assert queue.get_nowait() == _event()


async def test_event_is_discarded_when_the_transaction_rolls_back(session: AsyncSession) -> None:
    broker = LocalBroker()
    publisher = SessionEventPublisher(session, broker)

    async with broker.subscribe() as queue:
        publisher.publish(_event())
        await session.rollback()
        await session.commit()

        assert queue.empty()


async def test_booking_notifies_client_veterinarian_and_administration(
    client: AsyncClient, session: AsyncSession, broker: LocalBroker
) -> None:
    escenario = await montar(session)

    async with broker.subscribe() as queue:
        response = await client.post(
            URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
        )
        await asyncio.sleep(0)

        assert response.status_code == 201
        received = queue.get_nowait()
    assert received.topic == APPOINTMENTS_TOPIC
    assert received.user_ids == {escenario.cliente.id, escenario.veterinario.id}
    assert received.roles == {Role.ADMIN}
    assert received.reference_id == response.json()["id"]


async def test_a_rejected_booking_sends_nothing(
    client: AsyncClient, session: AsyncSession, broker: LocalBroker
) -> None:
    escenario = await montar(session, con_agenda=False)

    async with broker.subscribe() as queue:
        response = await client.post(
            URL, json=escenario.reserva(), headers=authorization_for(escenario.cliente)
        )
        await asyncio.sleep(0)

        assert response.status_code == 409
        assert queue.empty()


async def test_the_event_stream_requires_credentials(client: AsyncClient) -> None:
    response = await client.get(EVENTS_URL)

    assert response.status_code == 401

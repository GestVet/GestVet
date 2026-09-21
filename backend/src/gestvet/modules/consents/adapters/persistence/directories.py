"""Adaptadores de lectura hacia `pets`, `appointments` y `accounts`.

Consultas crudas contra tablas ajenas, acotadas a estas preguntas y cubiertas
por pruebas, igual que hacen los demás lectores cruzados del proyecto.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.consents.domain.appointment_facts import AppointmentFacts

_PET_IS_OWNED = text(
    "SELECT 1 FROM pets WHERE id = :pet_id AND owner_id = :owner_id AND is_active = :active"
)

_FIND_APPOINTMENT = text(
    "SELECT a.id, a.client_id, a.pet_id, a.veterinarian_id, a.status, t.is_emergency "
    "FROM appointments a JOIN appointment_types t ON t.id = a.appointment_type_id "
    "WHERE a.id = :appointment_id"
)

_PET_NAMES = text("SELECT id, name FROM pets WHERE id IN :ids").bindparams(
    bindparam("ids", expanding=True)
)

_USER_NAMES = text("SELECT id, first_name, last_name FROM users WHERE id IN :ids").bindparams(
    bindparam("ids", expanding=True)
)


class SqlPetDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def is_owned_by(self, pet_id: int, owner_id: int) -> bool:
        row = (
            await self._session.execute(
                _PET_IS_OWNED, {"pet_id": pet_id, "owner_id": owner_id, "active": True}
            )
        ).first()
        return row is not None


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(self, appointment_id: int) -> AppointmentFacts | None:
        row = (
            await self._session.execute(_FIND_APPOINTMENT, {"appointment_id": appointment_id})
        ).first()
        if row is None:
            return None
        return AppointmentFacts(
            id=row[0],
            client_id=row[1],
            pet_id=row[2],
            veterinarian_id=row[3],
            status=str(row[4]),
            is_emergency=bool(row[5]),
        )


class SqlNameDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def pet_names(self, pet_ids: Iterable[int]) -> dict[int, str]:
        ids = sorted(set(pet_ids))
        if not ids:
            return {}
        rows = await self._session.execute(_PET_NAMES, {"ids": ids})
        return {row[0]: str(row[1]) for row in rows}

    async def user_names(self, user_ids: Iterable[int]) -> dict[int, str]:
        ids = sorted(set(user_ids))
        if not ids:
            return {}
        rows = await self._session.execute(_USER_NAMES, {"ids": ids})
        return {row[0]: f"{row[1]} {row[2]}".strip() for row in rows}

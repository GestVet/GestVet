"""Adaptador del lector hacia `appointments`.

Consulta cruda contra la tabla ajena, acotada a esta única pregunta y
cubierta por pruebas, igual que hacen los demás lectores cruzados del
proyecto.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.complaints.ports.appointment_directory import (
    AppointmentDetails,
    ComplaintContext,
)

_FIND_DETAILS = text(
    "SELECT client_id, veterinarian_id FROM appointments WHERE id = :appointment_id"
)


# Una sola consulta para toda la página de reclamos, no una por reclamo.
_CONTEXTS = text(
    "SELECT a.id, a.scheduled_at, t.name AS type_name, p.name AS pet_name, "
    "c.first_name AS client_first, c.last_name AS client_last, "
    "v.first_name AS vet_first, v.last_name AS vet_last "
    "FROM appointments a "
    "JOIN appointment_types t ON t.id = a.appointment_type_id "
    "JOIN pets p ON p.id = a.pet_id "
    "JOIN users c ON c.id = a.client_id "
    "JOIN users v ON v.id = a.veterinarian_id "
    "WHERE a.id IN :ids"
).bindparams(bindparam("ids", expanding=True))


def _moment(value: datetime | str) -> datetime:
    # SQLite devuelve la fecha como texto y sin zona aunque se haya guardado en UTC.
    moment = datetime.fromisoformat(value) if isinstance(value, str) else value
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_details(self, appointment_id: int) -> AppointmentDetails | None:
        row = (
            await self._session.execute(_FIND_DETAILS, {"appointment_id": appointment_id})
        ).first()
        if row is None:
            return None
        return AppointmentDetails(
            client_id=int(row.client_id), veterinarian_id=int(row.veterinarian_id)
        )

    async def contexts_for(self, appointment_ids: list[int]) -> dict[int, ComplaintContext]:
        if not appointment_ids:
            return {}
        rows = await self._session.execute(_CONTEXTS, {"ids": sorted(set(appointment_ids))})
        return {
            int(row.id): ComplaintContext(
                client_name=f"{row.client_first} {row.client_last}".strip(),
                veterinarian_name=f"{row.vet_first} {row.vet_last}".strip(),
                pet_name=row.pet_name,
                appointment_type=row.type_name,
                scheduled_at=_moment(row.scheduled_at),
            )
            for row in rows
        }

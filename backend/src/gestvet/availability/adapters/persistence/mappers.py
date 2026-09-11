"""Traducción entre la fila y la entidad."""

from __future__ import annotations

from datetime import UTC, datetime

from gestvet.availability.adapters.persistence.models import AvailabilitySlotRow
from gestvet.availability.domain.entities import AvailabilitySlot


def _as_utc(moment: datetime) -> datetime:
    """SQLite no guarda la zona horaria; se repone al leer."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def row_to_entity(row: AvailabilitySlotRow) -> AvailabilitySlot:
    return AvailabilitySlot(
        id=row.id,
        veterinarian_id=row.veterinarian_id,
        starts_at=_as_utc(row.starts_at),
        ends_at=_as_utc(row.ends_at),
        created_at=_as_utc(row.created_at),
    )


def entity_to_row(slot: AvailabilitySlot) -> AvailabilitySlotRow:
    return AvailabilitySlotRow(
        veterinarian_id=slot.veterinarian_id,
        starts_at=slot.starts_at,
        ends_at=slot.ends_at,
        created_at=slot.created_at,
    )

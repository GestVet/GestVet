from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.availability.adapters.persistence.models import AvailabilitySlotRow
from gestvet.modules.availability.domain.entities import AvailabilitySlot


def row_to_entity(row: AvailabilitySlotRow) -> AvailabilitySlot:
    return AvailabilitySlot(
        id=row.id,
        veterinarian_id=row.veterinarian_id,
        starts_at=as_utc(row.starts_at),
        ends_at=as_utc(row.ends_at),
        created_at=as_utc(row.created_at),
    )


def entity_to_row(slot: AvailabilitySlot) -> AvailabilitySlotRow:
    return AvailabilitySlotRow(
        veterinarian_id=slot.veterinarian_id,
        starts_at=slot.starts_at,
        ends_at=slot.ends_at,
        created_at=slot.created_at,
    )

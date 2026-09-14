from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.availability.adapters.persistence.models import (
    AvailabilitySlotRow,
    ShiftChangeRequestRow,
)
from gestvet.modules.availability.domain.entities import (
    AvailabilitySlot,
    ChangeRequestStatus,
    ShiftChangeRequest,
    ShiftKind,
)


def row_to_entity(row: AvailabilitySlotRow) -> AvailabilitySlot:
    return AvailabilitySlot(
        id=row.id,
        veterinarian_id=row.veterinarian_id,
        starts_at=as_utc(row.starts_at),
        ends_at=as_utc(row.ends_at),
        kind=ShiftKind(row.kind),
        assigned_by=row.assigned_by_id,
        created_at=as_utc(row.created_at),
    )


def entity_to_row(slot: AvailabilitySlot) -> AvailabilitySlotRow:
    return AvailabilitySlotRow(
        veterinarian_id=slot.veterinarian_id,
        starts_at=slot.starts_at,
        ends_at=slot.ends_at,
        kind=slot.kind.value,
        assigned_by_id=slot.assigned_by,
        created_at=slot.created_at,
    )


def request_row_to_entity(row: ShiftChangeRequestRow) -> ShiftChangeRequest:
    return ShiftChangeRequest(
        id=row.id,
        veterinarian_id=row.veterinarian_id,
        slot_id=row.slot_id,
        message=row.message,
        status=ChangeRequestStatus(row.status),
        response=row.response,
        resolved_by=row.resolved_by_id,
        resolved_at=as_utc(row.resolved_at) if row.resolved_at else None,
        created_at=as_utc(row.created_at),
    )


def request_entity_to_row(request: ShiftChangeRequest) -> ShiftChangeRequestRow:
    return ShiftChangeRequestRow(
        veterinarian_id=request.veterinarian_id,
        slot_id=request.slot_id,
        message=request.message,
        status=request.status.value,
        response=request.response,
        resolved_by_id=request.resolved_by,
        resolved_at=request.resolved_at,
        created_at=request.created_at,
    )

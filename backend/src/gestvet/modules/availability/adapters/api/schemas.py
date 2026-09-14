from __future__ import annotations

from datetime import date, datetime, time

from pydantic import AwareDatetime, BaseModel, Field

from gestvet.modules.availability.domain.entities import (
    MAX_MESSAGE_LENGTH,
    MIN_MESSAGE_LENGTH,
    AvailabilitySlot,
    ChangeRequestStatus,
    ShiftChangeRequest,
    ShiftKind,
)
from gestvet.modules.availability.domain.weekly_plan import MAX_PLAN_WEEKS, WeeklyShift

# Tres turnos por día de la semana: mañana, tarde y guardia.
MAX_WEEKLY_SHIFTS = 21


class AssignShiftRequest(BaseModel):
    veterinarian_id: int = Field(ge=1)
    # `AwareDatetime` rechaza una marca sin zona en el borde. El dominio lo
    # vuelve a exigir, porque no todo consumidor entra por HTTP.
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    kind: ShiftKind = ShiftKind.REGULAR


class WeeklyShiftRequest(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0 es lunes y 6 domingo")
    starts: time
    ends: time = Field(description="Igual o anterior al inicio: termina al día siguiente")
    kind: ShiftKind = ShiftKind.REGULAR

    def to_domain(self) -> WeeklyShift:
        return WeeklyShift(weekday=self.weekday, starts=self.starts, ends=self.ends, kind=self.kind)


class WeeklyPlanRequest(BaseModel):
    veterinarian_id: int = Field(ge=1)
    first_day: date
    weeks: int = Field(ge=1, le=MAX_PLAN_WEEKS)
    shifts: list[WeeklyShiftRequest] = Field(min_length=1, max_length=MAX_WEEKLY_SHIFTS)


class SlotResponse(BaseModel):
    id: int
    veterinarian_id: int
    starts_at: datetime
    ends_at: datetime
    duration_minutes: int
    kind: ShiftKind
    assigned_by: int | None

    @classmethod
    def from_entity(cls, slot: AvailabilitySlot) -> SlotResponse:
        return cls(
            id=slot.id or 0,
            veterinarian_id=slot.veterinarian_id,
            starts_at=slot.starts_at,
            ends_at=slot.ends_at,
            duration_minutes=int(slot.duration.total_seconds() // 60),
            kind=slot.kind,
            assigned_by=slot.assigned_by,
        )


class SlotListResponse(BaseModel):
    items: list[SlotResponse]
    total: int


class CreateChangeRequest(BaseModel):
    message: str = Field(min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH)
    slot_id: int | None = Field(default=None, ge=1)


class ResolveChangeRequest(BaseModel):
    accepted: bool
    response: str = Field(default="", max_length=MAX_MESSAGE_LENGTH)


class ChangeRequestResponse(BaseModel):
    id: int
    veterinarian_id: int
    slot_id: int | None
    message: str
    status: ChangeRequestStatus
    response: str
    resolved_by: int | None
    resolved_at: datetime | None
    created_at: datetime

    @classmethod
    def from_entity(cls, request: ShiftChangeRequest) -> ChangeRequestResponse:
        return cls(
            id=request.id or 0,
            veterinarian_id=request.veterinarian_id,
            slot_id=request.slot_id,
            message=request.message,
            status=request.status,
            response=request.response,
            resolved_by=request.resolved_by,
            resolved_at=request.resolved_at,
            created_at=request.created_at,
        )


class ChangeRequestListResponse(BaseModel):
    items: list[ChangeRequestResponse]

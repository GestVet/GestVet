"""Contrato HTTP del módulo de disponibilidad."""

from __future__ import annotations

from datetime import datetime

from pydantic import AwareDatetime, BaseModel

from gestvet.availability.domain.entities import AvailabilitySlot


class PublishSlotRequest(BaseModel):
    # `AwareDatetime` rechaza una marca sin zona en el borde. El dominio lo
    # vuelve a exigir, porque no todo consumidor entra por HTTP.
    starts_at: AwareDatetime
    ends_at: AwareDatetime


class SlotResponse(BaseModel):
    id: int
    veterinarian_id: int
    starts_at: datetime
    ends_at: datetime
    duration_minutes: int

    @classmethod
    def from_entity(cls, slot: AvailabilitySlot) -> SlotResponse:
        return cls(
            id=slot.id or 0,
            veterinarian_id=slot.veterinarian_id,
            starts_at=slot.starts_at,
            ends_at=slot.ends_at,
            duration_minutes=int(slot.duration.total_seconds() // 60),
        )


class SlotListResponse(BaseModel):
    items: list[SlotResponse]
    total: int

"""Contrato HTTP del módulo de internaciones."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from gestvet.modules.hospitalizations.domain.entities import (
    MAX_DISCHARGE_NOTES_LENGTH,
    MAX_NOTE_LENGTH,
    MAX_REASON_LENGTH,
    Hospitalization,
    HospitalizationNote,
)


class OpenHospitalizationRequest(BaseModel):
    appointment_id: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=MAX_REASON_LENGTH)


class AddNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=MAX_NOTE_LENGTH)


class DischargeRequest(BaseModel):
    discharge_notes: str = Field(default="", max_length=MAX_DISCHARGE_NOTES_LENGTH)


class NoteResponse(BaseModel):
    id: int
    hospitalization_id: int
    author_id: int
    note: str
    created_at: datetime

    @classmethod
    def from_entity(cls, note: HospitalizationNote) -> NoteResponse:
        return cls(
            id=note.id or 0,
            hospitalization_id=note.hospitalization_id,
            author_id=note.author_id,
            note=note.note,
            created_at=note.created_at,
        )


class HospitalizationResponse(BaseModel):
    id: int
    appointment_id: int
    pet_id: int
    opened_by: int
    reason: str
    status: str
    status_label: str
    discharge_notes: str
    admitted_at: datetime
    discharged_at: datetime | None
    notes: list[NoteResponse]

    @classmethod
    def from_entity(
        cls, hospitalization: Hospitalization, notes: list[HospitalizationNote] | None = None
    ) -> HospitalizationResponse:
        return cls(
            id=hospitalization.id or 0,
            appointment_id=hospitalization.appointment_id,
            pet_id=hospitalization.pet_id,
            opened_by=hospitalization.opened_by,
            reason=hospitalization.reason,
            status=hospitalization.status.value,
            status_label=hospitalization.status.label,
            discharge_notes=hospitalization.discharge_notes,
            admitted_at=hospitalization.admitted_at,
            discharged_at=hospitalization.discharged_at,
            notes=[NoteResponse.from_entity(item) for item in notes or []],
        )


class HospitalizationPageResponse(BaseModel):
    items: list[HospitalizationResponse]
    total: int

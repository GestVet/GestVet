"""Contrato HTTP del módulo de historia clínica."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import AwareDatetime, BaseModel, Field

from gestvet.modules.medical_records.domain.attachment import Attachment
from gestvet.modules.medical_records.domain.entities import (
    MAX_DIAGNOSIS_LENGTH,
    MAX_NOTES_LENGTH,
    MAX_TREATMENT_LENGTH,
    ClinicalEntry,
    EntryKind,
)


class AddClinicalEntryRequest(BaseModel):
    pet_id: int = Field(ge=1)
    kind: EntryKind
    notes: str = Field(min_length=1, max_length=MAX_NOTES_LENGTH)
    diagnosis: str = Field(default="", max_length=MAX_DIAGNOSIS_LENGTH)
    treatment: str = Field(default="", max_length=MAX_TREATMENT_LENGTH)
    weight_kg: Decimal | None = Field(default=None, gt=0)
    appointment_id: int | None = Field(default=None, ge=1)
    occurred_at: AwareDatetime | None = None


class AttachmentResponse(BaseModel):
    id: int
    clinical_entry_id: int
    filename: str
    content_type: str
    size_bytes: int
    uploaded_by: int
    created_at: datetime

    @classmethod
    def from_entity(cls, attachment: Attachment) -> AttachmentResponse:
        return cls(
            id=attachment.id or 0,
            clinical_entry_id=attachment.clinical_entry_id,
            filename=attachment.filename,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            uploaded_by=attachment.uploaded_by,
            created_at=attachment.created_at,
        )


class ClinicalEntryResponse(BaseModel):
    id: int
    pet_id: int
    veterinarian_id: int
    appointment_id: int | None
    kind: EntryKind
    kind_label: str
    notes: str
    diagnosis: str
    treatment: str
    weight_kg: Decimal | None
    occurred_at: datetime
    created_at: datetime
    attachments: list[AttachmentResponse]

    @classmethod
    def from_entity(
        cls, entry: ClinicalEntry, attachments: list[Attachment] | None = None
    ) -> ClinicalEntryResponse:
        return cls(
            id=entry.id or 0,
            pet_id=entry.pet_id,
            veterinarian_id=entry.veterinarian_id,
            appointment_id=entry.appointment_id,
            kind=entry.kind,
            kind_label=entry.kind.label,
            notes=entry.notes,
            diagnosis=entry.diagnosis,
            treatment=entry.treatment,
            weight_kg=entry.weight_kg,
            occurred_at=entry.occurred_at,
            created_at=entry.created_at,
            attachments=[
                AttachmentResponse.from_entity(attachment) for attachment in attachments or []
            ],
        )


class ClinicalEntryPageResponse(BaseModel):
    items: list[ClinicalEntryResponse]
    total: int

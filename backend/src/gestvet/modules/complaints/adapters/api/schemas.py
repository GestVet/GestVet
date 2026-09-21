"""Contrato HTTP del módulo de reclamos."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from gestvet.modules.complaints.domain.entities import MAX_DESCRIPTION_LENGTH, Complaint
from gestvet.modules.complaints.domain.evidence import ComplaintEvidence
from gestvet.modules.complaints.ports.appointment_directory import ComplaintContext


class FileComplaintRequest(BaseModel):
    appointment_id: int = Field(ge=1)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)


class EvidenceResponse(BaseModel):
    id: int
    complaint_id: int
    filename: str
    content_type: str
    size_bytes: int
    uploaded_by: int
    created_at: datetime

    @classmethod
    def from_entity(cls, evidence: ComplaintEvidence) -> EvidenceResponse:
        return cls(
            id=evidence.id or 0,
            complaint_id=evidence.complaint_id,
            filename=evidence.filename,
            content_type=evidence.content_type,
            size_bytes=evidence.size_bytes,
            uploaded_by=evidence.uploaded_by,
            created_at=evidence.created_at,
        )


class ComplaintResponse(BaseModel):
    id: int
    client_id: int
    veterinarian_id: int
    appointment_id: int
    # Para leer el reclamo sin ir a buscar a quién corresponde cada número.
    client_name: str
    veterinarian_name: str
    pet_name: str
    appointment_type: str
    appointment_at: datetime | None
    description: str
    created_at: datetime
    evidence: list[EvidenceResponse]

    @classmethod
    def from_entity(
        cls,
        complaint: Complaint,
        evidence: list[ComplaintEvidence] | None = None,
        context: ComplaintContext | None = None,
    ) -> ComplaintResponse:
        return cls(
            id=complaint.id or 0,
            client_id=complaint.client_id,
            veterinarian_id=complaint.veterinarian_id,
            appointment_id=complaint.appointment_id,
            client_name=context.client_name if context else "",
            veterinarian_name=context.veterinarian_name if context else "",
            pet_name=context.pet_name if context else "",
            appointment_type=context.appointment_type if context else "",
            appointment_at=context.scheduled_at if context else None,
            description=complaint.description,
            created_at=complaint.created_at,
            evidence=[EvidenceResponse.from_entity(item) for item in evidence or []],
        )


class ComplaintPageResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int

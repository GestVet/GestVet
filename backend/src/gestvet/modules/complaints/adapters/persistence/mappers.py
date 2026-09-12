from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.complaints.adapters.persistence.models import (
    ComplaintEvidenceRow,
    ComplaintRow,
)
from gestvet.modules.complaints.domain.entities import Complaint
from gestvet.modules.complaints.domain.evidence import ComplaintEvidence


def row_to_entity(row: ComplaintRow) -> Complaint:
    return Complaint(
        id=row.id,
        client_id=row.client_id,
        veterinarian_id=row.veterinarian_id,
        appointment_id=row.appointment_id,
        description=row.description,
        created_at=as_utc(row.created_at),
    )


def entity_to_row(complaint: Complaint) -> ComplaintRow:
    return ComplaintRow(
        client_id=complaint.client_id,
        veterinarian_id=complaint.veterinarian_id,
        appointment_id=complaint.appointment_id,
        description=complaint.description,
        created_at=complaint.created_at,
    )


def evidence_row_to_entity(row: ComplaintEvidenceRow) -> ComplaintEvidence:
    return ComplaintEvidence(
        id=row.id,
        complaint_id=row.complaint_id,
        filename=row.filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        storage_key=row.storage_key,
        url=row.url,
        uploaded_by=row.uploaded_by,
        created_at=as_utc(row.created_at),
    )


def evidence_entity_to_row(evidence: ComplaintEvidence) -> ComplaintEvidenceRow:
    return ComplaintEvidenceRow(
        complaint_id=evidence.complaint_id,
        filename=evidence.filename,
        content_type=evidence.content_type,
        size_bytes=evidence.size_bytes,
        storage_key=evidence.storage_key,
        url=evidence.url,
        uploaded_by=evidence.uploaded_by,
        created_at=evidence.created_at,
    )

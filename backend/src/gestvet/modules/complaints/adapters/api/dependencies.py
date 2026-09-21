from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.attachments import create_attachment_storage
from gestvet.core.auth import SessionDep
from gestvet.modules.complaints.adapters.persistence.directories import SqlAppointmentDirectory
from gestvet.modules.complaints.adapters.persistence.repositories import (
    SqlAlchemyComplaintRepository,
    SqlAlchemyEvidenceRepository,
)
from gestvet.modules.complaints.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.complaints.ports.complaint_repository import ComplaintRepository
from gestvet.modules.complaints.ports.evidence_repository import EvidenceRepository
from gestvet.modules.complaints.ports.evidence_storage import EvidenceStorage


def get_complaint_repository(session: SessionDep) -> ComplaintRepository:
    return SqlAlchemyComplaintRepository(session)


def get_evidence_repository(session: SessionDep) -> EvidenceRepository:
    return SqlAlchemyEvidenceRepository(session)


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


def get_evidence_storage() -> EvidenceStorage:
    return create_attachment_storage()


ComplaintRepositoryDep = Annotated[ComplaintRepository, Depends(get_complaint_repository)]
EvidenceRepositoryDep = Annotated[EvidenceRepository, Depends(get_evidence_repository)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]
EvidenceStorageDep = Annotated[EvidenceStorage, Depends(get_evidence_storage)]

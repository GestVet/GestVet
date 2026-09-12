from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.attachments import LocalDiskAttachmentStorage
from gestvet.core.auth import SessionDep
from gestvet.core.config import get_settings
from gestvet.modules.medical_records.adapters.persistence.directories import SqlPetDirectory
from gestvet.modules.medical_records.adapters.persistence.repositories import (
    SqlAlchemyAttachmentRepository,
    SqlAlchemyClinicalEntryRepository,
)
from gestvet.modules.medical_records.ports.attachment_repository import AttachmentRepository
from gestvet.modules.medical_records.ports.attachment_storage import AttachmentStorage
from gestvet.modules.medical_records.ports.clinical_entry_repository import ClinicalEntryRepository
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory


def get_clinical_entry_repository(session: SessionDep) -> ClinicalEntryRepository:
    return SqlAlchemyClinicalEntryRepository(session)


def get_pet_directory(session: SessionDep) -> PetDirectory:
    return SqlPetDirectory(session)


def get_attachment_repository(session: SessionDep) -> AttachmentRepository:
    return SqlAlchemyAttachmentRepository(session)


def get_attachment_storage() -> AttachmentStorage:
    settings = get_settings()
    return LocalDiskAttachmentStorage(
        settings.attachments_storage_dir, f"{settings.api_base_url}/attachments"
    )


ClinicalEntryRepositoryDep = Annotated[
    ClinicalEntryRepository, Depends(get_clinical_entry_repository)
]
PetDirectoryDep = Annotated[PetDirectory, Depends(get_pet_directory)]
AttachmentRepositoryDep = Annotated[AttachmentRepository, Depends(get_attachment_repository)]
AttachmentStorageDep = Annotated[AttachmentStorage, Depends(get_attachment_storage)]

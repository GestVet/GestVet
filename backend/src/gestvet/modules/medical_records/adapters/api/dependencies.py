from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.medical_records.adapters.persistence.directories import SqlPetDirectory
from gestvet.modules.medical_records.adapters.persistence.repositories import (
    SqlAlchemyClinicalEntryRepository,
)
from gestvet.modules.medical_records.ports.clinical_entry_repository import ClinicalEntryRepository
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory


def get_clinical_entry_repository(session: SessionDep) -> ClinicalEntryRepository:
    return SqlAlchemyClinicalEntryRepository(session)


def get_pet_directory(session: SessionDep) -> PetDirectory:
    return SqlPetDirectory(session)


ClinicalEntryRepositoryDep = Annotated[
    ClinicalEntryRepository, Depends(get_clinical_entry_repository)
]
PetDirectoryDep = Annotated[PetDirectory, Depends(get_pet_directory)]

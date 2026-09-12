from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.hospitalizations.adapters.persistence.directories import (
    SqlAppointmentDirectory,
    SqlPetDirectory,
)
from gestvet.modules.hospitalizations.adapters.persistence.repositories import (
    SqlAlchemyHospitalizationRepository,
    SqlAlchemyNoteRepository,
)
from gestvet.modules.hospitalizations.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.hospitalizations.ports.hospitalization_repository import (
    HospitalizationRepository,
)
from gestvet.modules.hospitalizations.ports.note_repository import NoteRepository
from gestvet.modules.hospitalizations.ports.pet_directory import PetDirectory


def get_hospitalization_repository(session: SessionDep) -> HospitalizationRepository:
    return SqlAlchemyHospitalizationRepository(session)


def get_note_repository(session: SessionDep) -> NoteRepository:
    return SqlAlchemyNoteRepository(session)


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


def get_pet_directory(session: SessionDep) -> PetDirectory:
    return SqlPetDirectory(session)


HospitalizationRepositoryDep = Annotated[
    HospitalizationRepository, Depends(get_hospitalization_repository)
]
NoteRepositoryDep = Annotated[NoteRepository, Depends(get_note_repository)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]
PetDirectoryDep = Annotated[PetDirectory, Depends(get_pet_directory)]

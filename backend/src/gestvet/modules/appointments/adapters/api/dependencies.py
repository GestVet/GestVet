from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.appointments.adapters.persistence.directories import (
    SqlPetDirectory,
    SqlScheduleDirectory,
)
from gestvet.modules.appointments.adapters.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
    SqlAlchemyAppointmentTypeRepository,
)
from gestvet.modules.appointments.ports.repositories import (
    AppointmentRepository,
    AppointmentTypeRepository,
    PetDirectory,
    ScheduleDirectory,
)


def get_appointment_repository(session: SessionDep) -> AppointmentRepository:
    return SqlAlchemyAppointmentRepository(session)


def get_appointment_type_repository(session: SessionDep) -> AppointmentTypeRepository:
    return SqlAlchemyAppointmentTypeRepository(session)


def get_pet_directory(session: SessionDep) -> PetDirectory:
    return SqlPetDirectory(session)


def get_schedule_directory(session: SessionDep) -> ScheduleDirectory:
    return SqlScheduleDirectory(session)


AppointmentRepositoryDep = Annotated[AppointmentRepository, Depends(get_appointment_repository)]
AppointmentTypeRepositoryDep = Annotated[
    AppointmentTypeRepository, Depends(get_appointment_type_repository)
]
PetDirectoryDep = Annotated[PetDirectory, Depends(get_pet_directory)]
ScheduleDirectoryDep = Annotated[ScheduleDirectory, Depends(get_schedule_directory)]

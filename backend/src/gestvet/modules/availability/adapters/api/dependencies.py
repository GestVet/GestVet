from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.availability.adapters.persistence.directories import (
    SqlAppointmentDirectory,
    SqlVeterinarianDirectory,
)
from gestvet.modules.availability.adapters.persistence.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityRepository,
    SqlAlchemyShiftChangeRequestRepository,
)
from gestvet.modules.availability.ports.availability_repository import (
    AppointmentDirectory,
    AvailabilityRepository,
    ShiftChangeRequestRepository,
    VeterinarianDirectory,
)


def get_availability_repository(session: SessionDep) -> AvailabilityRepository:
    return SqlAlchemyAvailabilityRepository(session)


def get_change_request_repository(session: SessionDep) -> ShiftChangeRequestRepository:
    return SqlAlchemyShiftChangeRequestRepository(session)


def get_veterinarian_directory(session: SessionDep) -> VeterinarianDirectory:
    return SqlVeterinarianDirectory(session)


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


AvailabilityRepositoryDep = Annotated[AvailabilityRepository, Depends(get_availability_repository)]
ChangeRequestRepositoryDep = Annotated[
    ShiftChangeRequestRepository, Depends(get_change_request_repository)
]
VeterinarianDirectoryDep = Annotated[VeterinarianDirectory, Depends(get_veterinarian_directory)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]

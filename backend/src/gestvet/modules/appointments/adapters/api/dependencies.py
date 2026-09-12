from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.core.whatsapp import ConsoleWhatsAppSender, WhatsAppSender
from gestvet.modules.appointments.adapters.persistence.directories import (
    SqlClientDirectory,
    SqlPetDirectory,
    SqlScheduleDirectory,
)
from gestvet.modules.appointments.adapters.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
    SqlAlchemyAppointmentTypeRepository,
)
from gestvet.modules.appointments.ports.client_directory import ClientDirectory
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


def get_client_directory(session: SessionDep) -> ClientDirectory:
    return SqlClientDirectory(session)


def get_whatsapp_sender() -> WhatsAppSender:
    return ConsoleWhatsAppSender()


AppointmentRepositoryDep = Annotated[AppointmentRepository, Depends(get_appointment_repository)]
AppointmentTypeRepositoryDep = Annotated[
    AppointmentTypeRepository, Depends(get_appointment_type_repository)
]
PetDirectoryDep = Annotated[PetDirectory, Depends(get_pet_directory)]
ScheduleDirectoryDep = Annotated[ScheduleDirectory, Depends(get_schedule_directory)]
ClientDirectoryDep = Annotated[ClientDirectory, Depends(get_client_directory)]
WhatsAppSenderDep = Annotated[WhatsAppSender, Depends(get_whatsapp_sender)]

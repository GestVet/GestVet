from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import SessionDep
from gestvet.core.whatsapp import WhatsAppSender
from gestvet.core.whatsapp_console import ConsoleWhatsAppSender
from gestvet.modules.appointments.adapters.persistence.directories import (
    SqlAppointmentLabelDirectory,
    SqlClientDirectory,
    SqlPetDirectory,
    SqlRiskConsentDirectory,
    SqlScheduleDirectory,
)
from gestvet.modules.appointments.adapters.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
    SqlAlchemyAppointmentTypeRepository,
)
from gestvet.modules.appointments.ports.appointment_labels import AppointmentLabelDirectory
from gestvet.modules.appointments.ports.client_directory import ClientDirectory
from gestvet.modules.appointments.ports.repositories import (
    AppointmentRepository,
    AppointmentTypeRepository,
    PetDirectory,
    ScheduleDirectory,
)
from gestvet.modules.appointments.ports.risk_consent_directory import RiskConsentDirectory
from gestvet.modules.appointments.use_cases.change_status import ChangeAppointmentStatus


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


def get_appointment_label_directory(session: SessionDep) -> AppointmentLabelDirectory:
    return SqlAppointmentLabelDirectory(session)


def get_risk_consent_directory(session: SessionDep) -> RiskConsentDirectory:
    return SqlRiskConsentDirectory(session)


def get_whatsapp_sender() -> WhatsAppSender:
    return ConsoleWhatsAppSender()


AppointmentRepositoryDep = Annotated[AppointmentRepository, Depends(get_appointment_repository)]
AppointmentTypeRepositoryDep = Annotated[
    AppointmentTypeRepository, Depends(get_appointment_type_repository)
]
PetDirectoryDep = Annotated[PetDirectory, Depends(get_pet_directory)]
ScheduleDirectoryDep = Annotated[ScheduleDirectory, Depends(get_schedule_directory)]
ClientDirectoryDep = Annotated[ClientDirectory, Depends(get_client_directory)]
RiskConsentDirectoryDep = Annotated[RiskConsentDirectory, Depends(get_risk_consent_directory)]
WhatsAppSenderDep = Annotated[WhatsAppSender, Depends(get_whatsapp_sender)]
AppointmentLabelsDep = Annotated[
    AppointmentLabelDirectory, Depends(get_appointment_label_directory)
]


def get_change_status(
    appointments: AppointmentRepositoryDep,
    activity: ActivityRecorderDep,
    clients: ClientDirectoryDep,
    pets: PetDirectoryDep,
    whatsapp: WhatsAppSenderDep,
) -> ChangeAppointmentStatus:
    """Cambiar el estado de una cita, con todo lo que avisa al confirmarla."""
    return ChangeAppointmentStatus(appointments, activity, clients, pets, whatsapp)


ChangeStatusDep = Annotated[ChangeAppointmentStatus, Depends(get_change_status)]

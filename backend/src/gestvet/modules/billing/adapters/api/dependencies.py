from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.billing.adapters.persistence.directories import SqlAppointmentDirectory
from gestvet.modules.billing.adapters.persistence.repositories import SqlAlchemyPaymentRepository
from gestvet.modules.billing.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.billing.ports.payment_repository import PaymentRepository


def get_payment_repository(session: SessionDep) -> PaymentRepository:
    return SqlAlchemyPaymentRepository(session)


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


PaymentRepositoryDep = Annotated[PaymentRepository, Depends(get_payment_repository)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]

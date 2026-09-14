from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.core.whatsapp import WhatsAppSender
from gestvet.core.whatsapp_console import ConsoleWhatsAppSender
from gestvet.modules.billing.adapters.gateways.sandbox import SandboxPaymentGateway
from gestvet.modules.billing.adapters.persistence.directories import (
    SqlAppointmentDirectory,
    SqlClientDirectory,
)
from gestvet.modules.billing.adapters.persistence.repositories import (
    SqlAlchemyPaymentRepository,
    SqlAlchemyQrChargeRepository,
)
from gestvet.modules.billing.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.billing.ports.client_directory import ClientDirectory
from gestvet.modules.billing.ports.payment_gateway import PaymentGateway
from gestvet.modules.billing.ports.payment_repository import PaymentRepository
from gestvet.modules.billing.ports.qr_charge_repository import QrChargeRepository


def get_payment_repository(session: SessionDep) -> PaymentRepository:
    return SqlAlchemyPaymentRepository(session)


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


def get_client_directory(session: SessionDep) -> ClientDirectory:
    return SqlClientDirectory(session)


def get_qr_charge_repository(session: SessionDep) -> QrChargeRepository:
    return SqlAlchemyQrChargeRepository(session)


def get_payment_gateway() -> PaymentGateway:
    # Único adaptador hoy. Cuando exista una cuenta con Culqi, Izipay u otra
    # pasarela real, esta línea es lo único que cambia.
    return SandboxPaymentGateway()


def get_whatsapp_sender() -> WhatsAppSender:
    return ConsoleWhatsAppSender()


PaymentRepositoryDep = Annotated[PaymentRepository, Depends(get_payment_repository)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]
ClientDirectoryDep = Annotated[ClientDirectory, Depends(get_client_directory)]
QrChargeRepositoryDep = Annotated[QrChargeRepository, Depends(get_qr_charge_repository)]
PaymentGatewayDep = Annotated[PaymentGateway, Depends(get_payment_gateway)]
WhatsAppSenderDep = Annotated[WhatsAppSender, Depends(get_whatsapp_sender)]

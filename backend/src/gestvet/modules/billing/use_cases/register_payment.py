"""Caso de uso: registrar un pago hecho a mano (efectivo, Yape, transferencia)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.billing.domain.entities import Payment, PaymentMethod
from gestvet.modules.billing.domain.exceptions import AppointmentNotFound
from gestvet.modules.billing.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.billing.ports.payment_repository import PaymentRepository


@dataclass(frozen=True, slots=True)
class RegisterPaymentCommand:
    appointment_id: int
    amount: Decimal
    method: PaymentMethod
    registered_by: int
    reference: str = ""
    notes: str = ""


class RegisterPayment:
    def __init__(
        self,
        payments: PaymentRepository,
        appointments: AppointmentDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._payments = payments
        self._appointments = appointments
        self._activity = activity

    async def __call__(self, command: RegisterPaymentCommand) -> Payment:
        client_id = await self._appointments.find_client_id(command.appointment_id)
        if client_id is None:
            raise AppointmentNotFound(command.appointment_id)

        payment = Payment(
            appointment_id=command.appointment_id,
            client_id=client_id,
            amount=command.amount,
            method=command.method,
            registered_by=command.registered_by,
            reference=command.reference,
            notes=command.notes,
        )

        guardado = await self._payments.add(payment)
        await self._activity.record(
            command.registered_by,
            ActivityKind.PAYMENT_REGISTERED,
            f"S/ {guardado.amount} ({guardado.method.label}), cita {guardado.appointment_id}",
        )
        return guardado

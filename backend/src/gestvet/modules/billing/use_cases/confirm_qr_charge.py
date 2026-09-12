"""Caso de uso: confirmar un cobro por QR y registrar el pago.

Hoy lo dispara una acción explícita en la interfaz porque no hay pasarela
real detrás: es el mismo lugar donde, el día que la haya, se conecta el
webhook que esa pasarela llama para avisar que el cliente pagó. El caso de
uso no cambia; cambia quién lo invoca.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.whatsapp import WhatsAppSender
from gestvet.modules.billing.domain.entities import Payment, PaymentMethod
from gestvet.modules.billing.domain.exceptions import QrChargeNotFound
from gestvet.modules.billing.domain.qr_charge import QrCharge
from gestvet.modules.billing.ports.client_directory import ClientDirectory
from gestvet.modules.billing.ports.payment_repository import PaymentRepository
from gestvet.modules.billing.ports.qr_charge_repository import QrChargeRepository


@dataclass(frozen=True, slots=True)
class ConfirmQrChargeCommand:
    charge_id: int
    requester_id: int
    is_staff: bool


class ConfirmQrCharge:
    def __init__(
        self,
        charges: QrChargeRepository,
        payments: PaymentRepository,
        activity: ActivityRecorder,
        clients: ClientDirectory,
        whatsapp: WhatsAppSender,
    ) -> None:
        self._charges = charges
        self._payments = payments
        self._activity = activity
        self._clients = clients
        self._whatsapp = whatsapp

    async def __call__(self, command: ConfirmQrChargeCommand) -> QrCharge:
        charge = await self._charges.get(command.charge_id)
        if charge is None:
            raise QrChargeNotFound(command.charge_id)
        if not command.is_staff and charge.client_id != command.requester_id:
            raise QrChargeNotFound(command.charge_id)

        payment = Payment(
            appointment_id=charge.appointment_id,
            client_id=charge.client_id,
            amount=charge.amount,
            method=PaymentMethod.QR,
            registered_by=charge.client_id,
            reference=charge.gateway_charge_id,
        )
        guardado = await self._payments.add(payment)

        charge.confirm(guardado.id or 0)
        actualizado = await self._charges.save(charge)

        await self._activity.record(
            charge.client_id,
            ActivityKind.PAYMENT_REGISTERED,
            f"S/ {guardado.amount} (QR), cita {guardado.appointment_id}",
        )
        await self._notify_confirmed(charge.client_id, guardado.amount)
        return actualizado

    async def _notify_confirmed(self, client_id: int, amount: Decimal) -> None:
        contact = await self._clients.find_contact(client_id)
        if contact is None or not contact.phone:
            return
        await self._whatsapp.send_payment_confirmed(
            to=contact.phone, client_name=contact.name, amount=amount
        )

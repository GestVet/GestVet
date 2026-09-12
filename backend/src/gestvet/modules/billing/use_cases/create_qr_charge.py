"""Caso de uso: generar un QR para cobrar una cita."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.modules.billing.domain.exceptions import AppointmentNotFound
from gestvet.modules.billing.domain.qr_charge import QrCharge, QrChargeStatus
from gestvet.modules.billing.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.billing.ports.payment_gateway import PaymentGateway
from gestvet.modules.billing.ports.qr_charge_repository import QrChargeRepository


@dataclass(frozen=True, slots=True)
class CreateQrChargeCommand:
    appointment_id: int
    requester_id: int
    is_staff: bool


class CreateQrCharge:
    def __init__(
        self,
        charges: QrChargeRepository,
        appointments: AppointmentDirectory,
        gateway: PaymentGateway,
    ) -> None:
        self._charges = charges
        self._appointments = appointments
        self._gateway = gateway

    async def __call__(self, command: CreateQrChargeCommand) -> QrCharge:
        client_id = await self._appointments.find_client_id(command.appointment_id)
        if client_id is None:
            raise AppointmentNotFound(command.appointment_id)
        # Misma respuesta para "no existe" y "es de otro dueño": distinguirlas
        # confirmaría que el identificador pertenece a alguien.
        if not command.is_staff and client_id != command.requester_id:
            raise AppointmentNotFound(command.appointment_id)

        vigente = await self._charges.find_latest_for_appointment(command.appointment_id)
        if vigente is not None and vigente.effective_status() is QrChargeStatus.PENDING:
            return vigente

        amount = await self._appointments.find_amount_due(command.appointment_id)
        if amount is None:
            raise AppointmentNotFound(command.appointment_id)

        gateway_charge = await self._gateway.create_qr_charge(
            amount=amount, reference=f"Cita #{command.appointment_id}"
        )
        charge = QrCharge(
            appointment_id=command.appointment_id,
            client_id=client_id,
            amount=amount,
            gateway_charge_id=gateway_charge.gateway_charge_id,
            qr_image_data_url=gateway_charge.qr_image_data_url,
        )
        return await self._charges.add(charge)

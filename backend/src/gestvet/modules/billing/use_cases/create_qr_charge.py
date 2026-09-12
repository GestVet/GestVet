"""Caso de uso: generar un QR para cobrar una cita.

Por defecto cobra el precio de catálogo del tipo de cita. El personal puede
ajustarlo: en una cita normal, dentro de un margen acotado (el costo real de
un baño o una consulta no se aleja mucho del de lista); en una de
emergencia, sin margen, porque ahí el costo depende de lo que realmente hizo
falta y solo se sabe al terminar.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from gestvet.modules.billing.domain.exceptions import (
    AppointmentNotCompleted,
    AppointmentNotFound,
    CustomAmountRequiresStaff,
    InvalidPayment,
)
from gestvet.modules.billing.domain.qr_charge import QrCharge, QrChargeStatus
from gestvet.modules.billing.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.billing.ports.payment_gateway import PaymentGateway
from gestvet.modules.billing.ports.qr_charge_repository import QrChargeRepository

# Un baño de S/20 puede terminar costando 15 o 25 según el pelaje; una
# cirugía no. Por eso el margen solo aplica a citas que no son de emergencia.
NORMAL_APPOINTMENT_AMOUNT_TOLERANCE = Decimal("5")


@dataclass(frozen=True, slots=True)
class CreateQrChargeCommand:
    appointment_id: int
    requester_id: int
    is_staff: bool
    amount: Decimal | None = None


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

        if not await self._appointments.is_completed(command.appointment_id):
            raise AppointmentNotCompleted(command.appointment_id)

        vigente = await self._charges.find_latest_for_appointment(command.appointment_id)
        if vigente is not None and vigente.effective_status() is QrChargeStatus.PENDING:
            return vigente

        catalog_price = await self._appointments.find_amount_due(command.appointment_id)
        if catalog_price is None:
            raise AppointmentNotFound(command.appointment_id)

        amount = await self._resolve_amount(command, catalog_price)

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

    async def _resolve_amount(
        self, command: CreateQrChargeCommand, catalog_price: Decimal
    ) -> Decimal:
        if command.amount is None:
            return catalog_price
        if not command.is_staff:
            raise CustomAmountRequiresStaff(command.appointment_id)
        if not await self._appointments.is_emergency(command.appointment_id):
            _require_within_tolerance(command.amount, catalog_price)
        return command.amount


def _require_within_tolerance(amount: Decimal, catalog_price: Decimal) -> None:
    lower = catalog_price - NORMAL_APPOINTMENT_AMOUNT_TOLERANCE
    upper = catalog_price + NORMAL_APPOINTMENT_AMOUNT_TOLERANCE
    if amount < lower or amount > upper:
        raise InvalidPayment(
            f"Para una cita normal, el monto debe estar entre S/ {lower} y S/ {upper}."
        )

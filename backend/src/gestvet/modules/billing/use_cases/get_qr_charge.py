"""Caso de uso: consultar el estado de un cobro por QR."""

from __future__ import annotations

from gestvet.modules.billing.domain.exceptions import QrChargeNotFound
from gestvet.modules.billing.domain.qr_charge import QrCharge
from gestvet.modules.billing.ports.qr_charge_repository import QrChargeRepository


class GetQrCharge:
    def __init__(self, charges: QrChargeRepository) -> None:
        self._charges = charges

    async def __call__(self, charge_id: int, *, requester_id: int, is_staff: bool) -> QrCharge:
        charge = await self._charges.get(charge_id)
        if charge is None:
            raise QrChargeNotFound(charge_id)
        if not is_staff and charge.client_id != requester_id:
            raise QrChargeNotFound(charge_id)
        return charge

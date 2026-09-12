"""Puerto de persistencia de los cobros por QR.

Define qué necesita el negocio, nunca cómo se guarda.
"""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.billing.domain.qr_charge import QrCharge


class QrChargeRepository(Protocol):
    async def add(self, charge: QrCharge) -> QrCharge: ...

    async def get(self, charge_id: int) -> QrCharge | None: ...

    async def save(self, charge: QrCharge) -> QrCharge: ...

    async def find_latest_for_appointment(self, appointment_id: int) -> QrCharge | None: ...

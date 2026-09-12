"""Puerto de la pasarela de pago que genera el QR de cobro.

El caso de uso pide un cobro por un monto y recibe un QR para mostrar; no
sabe si detrás hay una pasarela real (Culqi, Izipay, u otra) o, como hoy, un
adaptador de prueba que simula la confirmación. Cambiar de una a otra es
reemplazar el adaptador, sin tocar ningún caso de uso.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GatewayCharge:
    gateway_charge_id: str
    qr_image_data_url: str


class PaymentGateway(Protocol):
    async def create_qr_charge(self, *, amount: Decimal, reference: str) -> GatewayCharge: ...

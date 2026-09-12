"""Adaptador de prueba de la pasarela de pago.

Genera un QR real (se puede escanear y leer como texto) pero no hay banco
detrás: la confirmación la dispara una acción explícita en la interfaz en vez
de un webhook. Sirve para desarrollar y probar el circuito completo sin
depender de una cuenta con Culqi, Izipay o el proveedor que se elija más
adelante.

Se reemplaza por un adaptador que hable con la pasarela real sin tocar
ningún caso de uso: el puerto no cambia. Ese adaptador sí necesita un
extremo HTTP que reciba el webhook del proveedor y llame a `ConfirmQrCharge`
cuando avise que el cliente pagó, en vez de exponerlo como una acción de la
interfaz.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from gestvet.core.qrcode_image import render_qr_png_data_url
from gestvet.modules.billing.ports.payment_gateway import GatewayCharge


class SandboxPaymentGateway:
    async def create_qr_charge(self, *, amount: Decimal, reference: str) -> GatewayCharge:
        gateway_charge_id = f"sandbox-{uuid.uuid4().hex}"
        payload = f"GestVet | {reference} | S/ {amount} | ref:{gateway_charge_id}"
        return GatewayCharge(
            gateway_charge_id=gateway_charge_id,
            qr_image_data_url=render_qr_png_data_url(payload),
        )

"""Errores de dominio de los pagos.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class BillingError(Exception):
    """Raíz de los errores del módulo de pagos."""


class InvalidPayment(BillingError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class PaymentNotFound(BillingError):
    def __init__(self, payment_id: int) -> None:
        super().__init__(f"No existe el pago {payment_id}.")
        self.payment_id = payment_id


class PaymentAlreadyVoided(BillingError):
    def __init__(self, payment_id: int) -> None:
        super().__init__(f"El pago {payment_id} ya estaba anulado.")
        self.payment_id = payment_id


class AppointmentNotFound(BillingError):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"No existe la cita {appointment_id}.")
        self.appointment_id = appointment_id

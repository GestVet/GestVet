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


class QrChargeNotFound(BillingError):
    def __init__(self, charge_id: int) -> None:
        super().__init__(f"No existe el cobro {charge_id}.")
        self.charge_id = charge_id


class QrChargeNotPending(BillingError):
    def __init__(self, charge_id: int) -> None:
        super().__init__(f"El cobro {charge_id} ya no está pendiente.")
        self.charge_id = charge_id


class AppointmentNotCompleted(BillingError):
    """El precio del QR es fijo: solo corresponde una vez atendida la cita.

    Si el desenlace amerita cobrar distinto, o no cobrar, esa decisión la
    toma el personal a mano por `RegisterPayment`, no el cliente por QR.
    """

    def __init__(self, appointment_id: int) -> None:
        super().__init__(
            f"La cita {appointment_id} todavía no fue completada. "
            "El cobro por QR se genera después de la atención."
        )
        self.appointment_id = appointment_id


class CustomAmountRequiresStaff(BillingError):
    """Un cliente nunca fija su propio monto: solo el personal puede ajustarlo."""

    def __init__(self, appointment_id: int) -> None:
        super().__init__("Solo el personal puede fijar un monto distinto al de catálogo.")
        self.appointment_id = appointment_id

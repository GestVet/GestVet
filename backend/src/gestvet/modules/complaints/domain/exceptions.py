"""Errores de dominio de reclamos.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class ComplaintsError(Exception):
    """Raíz de los errores del módulo de reclamos."""


class InvalidComplaint(ComplaintsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class InvalidEvidence(ComplaintsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class AppointmentNotFound(ComplaintsError):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"No existe la cita {appointment_id}.")
        self.appointment_id = appointment_id


class ComplaintNotFound(ComplaintsError):
    def __init__(self, complaint_id: int) -> None:
        super().__init__(f"No existe el reclamo {complaint_id}.")
        self.complaint_id = complaint_id

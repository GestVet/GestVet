"""Errores de dominio de internaciones.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class HospitalizationsError(Exception):
    """Raíz de los errores del módulo de internaciones."""


class InvalidHospitalization(HospitalizationsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class HospitalizationNotFound(HospitalizationsError):
    def __init__(self, hospitalization_id: int) -> None:
        super().__init__(f"No existe la internación {hospitalization_id}.")
        self.hospitalization_id = hospitalization_id


class HospitalizationAlreadyDischarged(HospitalizationsError):
    def __init__(self, hospitalization_id: int) -> None:
        super().__init__(f"La internación {hospitalization_id} ya tiene alta médica.")
        self.hospitalization_id = hospitalization_id


class AppointmentNotFound(HospitalizationsError):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"No existe la cita {appointment_id}.")
        self.appointment_id = appointment_id


class PetNotFound(HospitalizationsError):
    def __init__(self, pet_id: int) -> None:
        super().__init__(f"No existe la mascota {pet_id}.")
        self.pet_id = pet_id


class HospitalizationConsentMissing(HospitalizationsError):
    def __init__(self) -> None:
        super().__init__(
            "Para internar hace falta el consentimiento de internación aceptado por el "
            "responsable. Pedíselo desde la pestaña Consentimientos de la cita. Si es una "
            "emergencia, la vida de la mascota corre peligro y no hay forma de ubicarlo, "
            "registrá ahí la atención sin consentimiento por urgencia vital."
        )

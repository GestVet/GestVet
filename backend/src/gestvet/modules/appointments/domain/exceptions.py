"""Errores de dominio de citas.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class AppointmentsError(Exception):
    """Raíz de los errores del módulo de citas."""


class InvalidAppointment(AppointmentsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class AppointmentNotFound(AppointmentsError):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"No existe la cita {appointment_id}.")
        self.appointment_id = appointment_id


class AppointmentTypeNotFound(AppointmentsError):
    def __init__(self, type_id: int) -> None:
        super().__init__(f"No existe el tipo de cita {type_id}.")
        self.type_id = type_id


class PetNotOwned(AppointmentsError):
    def __init__(self, pet_id: int) -> None:
        super().__init__(f"La mascota {pet_id} no está entre las tuyas.")
        self.pet_id = pet_id


class VeterinarianUnavailable(AppointmentsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class OutsideAvailability(AppointmentsError):
    def __init__(self) -> None:
        super().__init__("El horario elegido está fuera de la disponibilidad del veterinario.")


class OverlappingAppointment(AppointmentsError):
    def __init__(self) -> None:
        super().__init__("El horario elegido se superpone con otra cita.")


class NoEmergencyVeterinarian(AppointmentsError):
    def __init__(self) -> None:
        super().__init__(
            "No hay un veterinario de emergencia disponible en este momento. "
            "Comunicate con la clínica por teléfono."
        )


class IllegalStatusChange(AppointmentsError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Una cita {current} no puede pasar a {target}.")
        self.current = current
        self.target = target

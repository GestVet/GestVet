"""Errores de dominio de consentimientos.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class ConsentsError(Exception):
    """Raíz de los errores del módulo de consentimientos."""


class InvalidSignerName(ConsentsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class InvalidConsent(ConsentsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class TemplateNotFound(ConsentsError):
    def __init__(self, template_id: int | None = None) -> None:
        super().__init__(
            f"No existe el texto de consentimiento {template_id}."
            if template_id is not None
            else "No hay un texto de consentimiento vigente para ese tipo."
        )
        self.template_id = template_id


class TemplateOutdated(ConsentsError):
    """Se firmó sobre un texto que ya fue reemplazado por otra versión."""

    def __init__(self) -> None:
        super().__init__(
            "El texto del consentimiento se actualizó mientras lo leías. "
            "Volvé a leerlo y firmalo de nuevo."
        )


class PetNotOwned(ConsentsError):
    def __init__(self, pet_id: int) -> None:
        super().__init__(f"La mascota {pet_id} no está entre las del cliente.")
        self.pet_id = pet_id


class ConsentNotFound(ConsentsError):
    def __init__(self, consent_id: int) -> None:
        super().__init__(f"No existe el consentimiento {consent_id}.")
        self.consent_id = consent_id


class InvalidConsentDetails(ConsentsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class InvalidWaiver(ConsentsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class KindNotRequestable(ConsentsError):
    """El riesgo de emergencia lo firma el dueño al abrirla; no lo pide el veterinario."""

    def __init__(self) -> None:
        super().__init__("Ese tipo de consentimiento no se pide desde una cita.")


class AppointmentNotFound(ConsentsError):
    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"No existe la cita {appointment_id}.")
        self.appointment_id = appointment_id


class AppointmentRequired(ConsentsError):
    def __init__(self) -> None:
        super().__init__("Indicá la cita de la que querés ver los consentimientos.")


class AppointmentCancelled(ConsentsError):
    def __init__(self) -> None:
        super().__init__("La cita está cancelada: no se le piden consentimientos.")


class WaiverOnlyForEmergencies(ConsentsError):
    def __init__(self) -> None:
        super().__init__(
            "Atender sin consentimiento solo se admite en una emergencia. "
            "En una cita común, pedí el consentimiento y esperá la respuesta."
        )


class PendingRequestExists(ConsentsError):
    def __init__(self) -> None:
        super().__init__("Ya hay un pedido de ese consentimiento esperando respuesta en esta cita.")


class ConsentNotPending(ConsentsError):
    def __init__(self, status_label: str) -> None:
        super().__init__(f"El consentimiento ya no espera respuesta: está {status_label.lower()}.")
        self.status_label = status_label


class ConsentExpired(ConsentsError):
    def __init__(self) -> None:
        super().__init__(
            "El pedido de consentimiento venció sin respuesta. "
            "Hace falta que el veterinario lo vuelva a pedir."
        )

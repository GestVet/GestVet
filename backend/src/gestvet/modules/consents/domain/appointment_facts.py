"""Lo que hace falta saber de una cita para pedir sobre ella un consentimiento.

La cita es de `appointments` y este módulo no puede importar su dominio: llega
como hechos sueltos, con el estado y el tipo como texto.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.modules.consents.domain.exceptions import (
    AppointmentCancelled,
    AppointmentNotFound,
    WaiverOnlyForEmergencies,
)

# El valor que guarda `appointments`, repetido a mano porque su dominio no se
# puede importar. Si allá cambia, las pruebas del flujo completo lo notan.
CANCELLED_STATUS = "cancelled"


@dataclass(frozen=True, slots=True)
class AppointmentFacts:
    id: int
    client_id: int
    pet_id: int
    veterinarian_id: int
    status: str
    is_emergency: bool

    def ensure_open_for_consents(self) -> None:
        if self.status == CANCELLED_STATUS:
            raise AppointmentCancelled()

    def ensure_emergency(self) -> None:
        # La excepción vale para salvar una vida, no para ahorrarse la espera
        # de una cita programada: fuera de una emergencia siempre se pide.
        if not self.is_emergency:
            raise WaiverOnlyForEmergencies()


def ensure_visible(
    facts: AppointmentFacts | None, appointment_id: int, *, user_id: int, sees_all: bool
) -> AppointmentFacts:
    """La cita, si quien pregunta la atiende o ve todas.

    Una ajena responde igual que una inexistente, como en el resto de la API.
    """
    if facts is None or not (sees_all or facts.veterinarian_id == user_id):
        raise AppointmentNotFound(appointment_id)
    return facts

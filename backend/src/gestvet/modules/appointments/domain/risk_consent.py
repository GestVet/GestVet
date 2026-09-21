"""Cuándo una aceptación de riesgo habilita abrir una emergencia.

La regla vive acá y no en `consents`: es este módulo el que decide qué le
alcanza para abrir una emergencia. De `consents` solo se leen los hechos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from gestvet.modules.appointments.domain.exceptions import RiskConsentRejected

# Los valores que guarda `consents`, repetidos a mano porque su dominio no se
# puede importar. Si allá cambian, las pruebas del flujo completo lo notan.
EMERGENCY_RISK_KIND = "emergency_risk"
ACCEPTED_STATUS = "accepted"

# Lo que puede pasar entre firmar y abrir: alcanza para reintentar si la
# apertura falló, y no deja que una firma vieja habilite una emergencia nueva
# sin que el dueño vuelva a leer el texto.
RISK_CONSENT_VALIDITY = timedelta(minutes=30)


@dataclass(frozen=True, slots=True)
class RiskConsentFacts:
    """Lo que hace falta de un consentimiento para decidir si habilita una emergencia.

    `kind` y `status` llegan como texto: los enumerados son de `consents` y
    este módulo no puede importarlos.
    """

    kind: str
    status: str
    client_id: int
    pet_id: int
    decided_at: datetime
    used_by_appointment: bool


def ensure_risk_consent_usable(
    facts: RiskConsentFacts | None, *, client_id: int, pet_id: int, now: datetime
) -> None:
    """Falla con un motivo legible si el consentimiento no sirve para esta emergencia.

    Uno ajeno o inexistente dan el mismo mensaje, para no confirmar que el
    identificador es de otro cliente.
    """
    if (
        facts is None
        or facts.client_id != client_id
        or facts.kind != EMERGENCY_RISK_KIND
        or facts.status != ACCEPTED_STATUS
    ):
        raise RiskConsentRejected(
            "No encontramos la aceptación del riesgo de esta emergencia. Leé el texto y firmalo."
        )
    if facts.pet_id != pet_id:
        raise RiskConsentRejected(
            "La aceptación del riesgo que firmaste es para otra mascota. Firmala para esta."
        )
    if facts.used_by_appointment:
        raise RiskConsentRejected(
            "Esa aceptación del riesgo ya se usó para abrir otra emergencia. Firmala de nuevo."
        )
    if now - facts.decided_at > RISK_CONSENT_VALIDITY:
        minutos = int(RISK_CONSENT_VALIDITY.total_seconds() // 60)
        raise RiskConsentRejected(
            f"La aceptación del riesgo se firmó hace más de {minutos} minutos. "
            "Volvé a leer el texto y firmalo de nuevo."
        )

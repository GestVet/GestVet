"""Lector hacia datos que posee `consents`.

Una emergencia se abre solo con la aceptación del riesgo firmada por el
dueño. `consents` es otro módulo de dominio y este no puede importarlo: la
pregunta se declara acá y un adaptador la responde leyendo la tabla ajena.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.appointments.domain.risk_consent import RiskConsentFacts


class RiskConsentDirectory(Protocol):
    async def find(self, consent_id: int) -> RiskConsentFacts | None:
        """El consentimiento y si alguna cita ya lo usó, o `None` si no existe."""
        ...

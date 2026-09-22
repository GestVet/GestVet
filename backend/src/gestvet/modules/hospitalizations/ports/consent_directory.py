"""Lector hacia datos que posee `consents`.

Internar es un procedimiento que puede esperar a que el dueño responda: sin
su consentimiento de internación, o sin la constancia de que se atendió sin él
por urgencia vital, no se abre. `consents` es otro módulo de dominio y este no
puede importarlo: la pregunta se declara acá como puerto y un adaptador la
responde leyendo la tabla ajena.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from typing import Protocol


class ConsentDirectory(Protocol):
    async def allows_hospitalization(self, appointment_id: int) -> bool:
        """Si la cita tiene el consentimiento de internación aceptado o eximido por urgencia."""
        ...

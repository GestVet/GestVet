"""Lector hacia datos que posee `appointments`.

Un consentimiento que pide el veterinario cuelga de una cita: de ella salen el
cliente y la mascota, y ella dice si es una emergencia, que es lo único que
habilita atender sin consentimiento. `appointments` es otro módulo de dominio
y este no puede importarlo: la pregunta se declara acá como puerto y un
adaptador la responde leyendo la tabla ajena.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.consents.domain.appointment_facts import AppointmentFacts


class AppointmentDirectory(Protocol):
    async def find(self, appointment_id: int) -> AppointmentFacts | None: ...

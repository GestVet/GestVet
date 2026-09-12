"""Lector hacia datos que posee `appointments`.

Reseñar a un veterinario exige haber tenido, de verdad, una cita completada
con él: si no, cualquiera podría calificar a cualquiera. `appointments` es
otro módulo de dominio y este no puede importarlo: la pregunta se declara
acá como puerto y un adaptador la responde leyendo la tabla ajena, igual que
hacen `billing` y `medical_records`.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from typing import Protocol


class AppointmentDirectory(Protocol):
    async def has_completed_appointment(self, client_id: int, veterinarian_id: int) -> bool: ...

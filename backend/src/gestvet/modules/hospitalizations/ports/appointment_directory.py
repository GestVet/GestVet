"""Lector hacia datos que posee `appointments`.

Abrir una internación necesita saber de qué mascota es la cita: la fija la
cita, no quien la abre, para que una internación no quede huérfana de una
mascota que nunca existió. `appointments` es otro módulo de dominio y este
no puede importarlo: la pregunta se declara acá como puerto y un adaptador
la responde leyendo la tabla ajena.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from typing import Protocol


class AppointmentDirectory(Protocol):
    async def find_pet_id(self, appointment_id: int) -> int | None: ...

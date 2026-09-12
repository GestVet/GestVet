"""Lector hacia datos que posee `appointments`.

Un reclamo se ata a una cita puntual, y el veterinario reclamado es el que
la atendió, no el que el cliente escriba: eso evita que alguien le reclame a
un veterinario que nunca lo tocó. `appointments` es otro módulo de dominio y
este no puede importarlo: la pregunta se declara acá como puerto y un
adaptador la responde leyendo la tabla ajena.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AppointmentDetails:
    client_id: int
    veterinarian_id: int


class AppointmentDirectory(Protocol):
    async def find_details(self, appointment_id: int) -> AppointmentDetails | None: ...

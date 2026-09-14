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
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AppointmentDetails:
    client_id: int
    veterinarian_id: int


@dataclass(frozen=True, slots=True)
class ComplaintContext:
    """Lo que hace legible un reclamo: quién, sobre quién, de qué mascota y qué cita."""

    client_name: str
    veterinarian_name: str
    pet_name: str
    appointment_type: str
    scheduled_at: datetime


class AppointmentDirectory(Protocol):
    async def find_details(self, appointment_id: int) -> AppointmentDetails | None: ...

    async def contexts_for(self, appointment_ids: list[int]) -> dict[int, ComplaintContext]:
        """El contexto de varias citas en una sola lectura, por identificador de cita."""
        ...

"""Lector hacia datos que posee `appointments`.

Registrar un pago necesita saber si la cita existe y de qué cliente es, para
completar el pago y para poder acotar "mis pagos" a quien corresponde.
`appointments` es otro módulo de dominio y este no puede importarlo: la
pregunta se declara acá como puerto y un adaptador la responde leyendo la
tabla ajena, igual que hacen `medical_records` y `accounts`.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from typing import Protocol


class AppointmentDirectory(Protocol):
    async def find_client_id(self, appointment_id: int) -> int | None: ...

"""Lector hacia datos que posee `appointments`.

Poner a alguien de guardia no puede dejar huérfana una cita normal que ya
tenía asignada. `accounts` no puede importar `appointments` -son dos módulos
de dominio independientes-, así que la pregunta se declara acá como puerto y
un adaptador la responde leyendo la tabla ajena, igual que hace `appointments`
con `pets` y `availability`. Se lee, nunca se escribe.
"""

from __future__ import annotations

from typing import Protocol


class AppointmentDirectory(Protocol):
    """Lo que las cuentas necesitan saber de las citas: si tiene alguna pendiente."""

    async def has_upcoming_normal_appointments(self, veterinarian_id: int) -> bool: ...

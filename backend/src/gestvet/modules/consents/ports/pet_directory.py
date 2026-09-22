"""Lector hacia datos que posee `pets`.

Un consentimiento lo firma el dueño de la mascota, o el personal en su
nombre, y nunca sobre el animal de otro. `pets` es otro módulo de dominio y
este no puede importarlo: la pregunta se declara acá como puerto y un
adaptador la responde leyendo la tabla ajena.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from typing import Protocol


class PetDirectory(Protocol):
    async def is_owned_by(self, pet_id: int, owner_id: int) -> bool:
        """Si la mascota está activa y es de ese cliente."""
        ...

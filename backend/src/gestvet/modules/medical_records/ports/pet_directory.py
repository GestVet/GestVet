"""Lector hacia datos que posee `pets`.

Una entrada clínica necesita saber si la mascota existe y de quién es, para
autorizar la lectura del cliente. `pets` es otro módulo de dominio y este no
puede importarlo: la pregunta se declara acá como puerto y un adaptador la
responde leyendo la tabla ajena, igual que hace `appointments`.

Se lee, nunca se escribe.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PetSummary:
    name: str
    species: str
    breed: str
    owner_name: str
    sex_label: str
    color: str
    microchip_number: str
    temperament: str
    weight_kg: Decimal | None
    height_cm: Decimal | None
    is_sterilized: bool | None
    allergies: str


class PetDirectory(Protocol):
    async def exists(self, pet_id: int) -> bool: ...

    async def is_owned_by(self, pet_id: int, owner_id: int) -> bool: ...

    async def summary(self, pet_id: int) -> PetSummary | None: ...

"""Lector hacia datos que posee `reviews`.

Un cliente que elige veterinario para reservar quiere ver, de un vistazo,
qué tan bien atiende cada uno. `accounts` no puede importar `reviews` -son
dos módulos de dominio independientes-, así que la pregunta se declara acá
como puerto y un adaptador la responde leyendo la tabla ajena. Se lee, nunca
se escribe.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RatingSummary:
    average: Decimal | None
    count: int


class ReviewsDirectory(Protocol):
    async def summaries_for(self, veterinarian_ids: list[int]) -> dict[int, RatingSummary]: ...

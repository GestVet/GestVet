"""Puerto de persistencia de reseñas.

Define qué necesita el negocio, nunca cómo se guarda.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page
from gestvet.modules.reviews.domain.entities import Review


@dataclass(frozen=True, slots=True)
class ReviewQuery:
    veterinarian_id: int
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


@dataclass(frozen=True, slots=True)
class RatingSummary:
    average: Decimal | None
    count: int


class ReviewRepository(Protocol):
    async def add(self, review: Review) -> Review: ...

    async def save(self, review: Review) -> Review: ...

    async def find_by_client_and_veterinarian(
        self, client_id: int, veterinarian_id: int
    ) -> Review | None: ...

    async def search(self, query: ReviewQuery) -> Page[Review]: ...

    async def summary_for(self, veterinarian_id: int) -> RatingSummary: ...

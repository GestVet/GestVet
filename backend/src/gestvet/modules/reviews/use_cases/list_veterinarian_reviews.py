"""Caso de uso: consultar las reseñas de un veterinario y su promedio."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.pagination import Page
from gestvet.modules.reviews.domain.entities import Review
from gestvet.modules.reviews.ports.review_repository import (
    RatingSummary,
    ReviewQuery,
    ReviewRepository,
)


@dataclass(frozen=True, slots=True)
class VeterinarianReviews:
    summary: RatingSummary
    page: Page[Review]


class ListVeterinarianReviews:
    def __init__(self, reviews: ReviewRepository) -> None:
        self._reviews = reviews

    async def __call__(self, query: ReviewQuery) -> VeterinarianReviews:
        summary = await self._reviews.summary_for(query.veterinarian_id)
        page = await self._reviews.search(query)
        return VeterinarianReviews(summary=summary, page=page)

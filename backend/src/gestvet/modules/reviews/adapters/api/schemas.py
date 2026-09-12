"""Contrato HTTP del módulo de reseñas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from gestvet.modules.reviews.domain.entities import (
    MAX_COMMENT_LENGTH,
    MAX_RATING,
    MIN_RATING,
    Review,
)
from gestvet.modules.reviews.ports.review_repository import RatingSummary
from gestvet.modules.reviews.use_cases.list_veterinarian_reviews import VeterinarianReviews


class SubmitReviewRequest(BaseModel):
    veterinarian_id: int = Field(ge=1)
    rating: int = Field(ge=MIN_RATING, le=MAX_RATING)
    comment: str = Field(min_length=1, max_length=MAX_COMMENT_LENGTH)


class ReviewResponse(BaseModel):
    id: int
    veterinarian_id: int
    client_id: int
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, review: Review) -> ReviewResponse:
        return cls(
            id=review.id or 0,
            veterinarian_id=review.veterinarian_id,
            client_id=review.client_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )


class RatingSummaryResponse(BaseModel):
    average: Decimal | None
    count: int

    @classmethod
    def from_entity(cls, summary: RatingSummary) -> RatingSummaryResponse:
        return cls(average=summary.average, count=summary.count)


class VeterinarianReviewsResponse(BaseModel):
    summary: RatingSummaryResponse
    items: list[ReviewResponse]
    total: int

    @classmethod
    def from_result(cls, result: VeterinarianReviews) -> VeterinarianReviewsResponse:
        return cls(
            summary=RatingSummaryResponse.from_entity(result.summary),
            items=[ReviewResponse.from_entity(item) for item in result.page.items],
            total=result.page.total,
        )

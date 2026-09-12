from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.reviews.adapters.persistence.models import ReviewRow
from gestvet.modules.reviews.domain.entities import Review


def row_to_entity(row: ReviewRow) -> Review:
    return Review(
        id=row.id,
        veterinarian_id=row.veterinarian_id,
        client_id=row.client_id,
        rating=row.rating,
        comment=row.comment,
        created_at=as_utc(row.created_at),
        updated_at=as_utc(row.updated_at),
    )


def entity_to_row(review: Review) -> ReviewRow:
    return ReviewRow(
        veterinarian_id=review.veterinarian_id,
        client_id=review.client_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )

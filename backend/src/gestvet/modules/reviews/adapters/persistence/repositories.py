from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.pagination import Page
from gestvet.modules.reviews.adapters.persistence.mappers import entity_to_row, row_to_entity
from gestvet.modules.reviews.adapters.persistence.models import ReviewRow
from gestvet.modules.reviews.domain.entities import Review
from gestvet.modules.reviews.ports.review_repository import RatingSummary, ReviewQuery


class SqlAlchemyReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, review: Review) -> Review:
        row = entity_to_row(review)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_entity(row)

    async def save(self, review: Review) -> Review:
        row = await self._session.get(ReviewRow, review.id)
        if row is None:
            raise ValueError(f"La reseña {review.id} ya no existe.")
        row.rating = review.rating
        row.comment = review.comment
        row.updated_at = review.updated_at
        await self._session.flush()
        return row_to_entity(row)

    async def find_by_client_and_veterinarian(
        self, client_id: int, veterinarian_id: int
    ) -> Review | None:
        row = (
            await self._session.execute(
                select(ReviewRow).where(
                    ReviewRow.client_id == client_id,
                    ReviewRow.veterinarian_id == veterinarian_id,
                )
            )
        ).scalar_one_or_none()
        return row_to_entity(row) if row else None

    async def search(self, query: ReviewQuery) -> Page[Review]:
        base = select(ReviewRow).where(ReviewRow.veterinarian_id == query.veterinarian_id)

        total = int(
            (
                await self._session.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
        )
        rows = await self._session.execute(
            base.order_by(ReviewRow.created_at.desc(), ReviewRow.id.desc())
            .limit(query.limit)
            .offset(query.offset)
        )
        return Page(items=[row_to_entity(row) for row in rows.scalars().all()], total=total)

    async def summary_for(self, veterinarian_id: int) -> RatingSummary:
        row = (
            await self._session.execute(
                select(func.avg(ReviewRow.rating), func.count())
                .select_from(ReviewRow)
                .where(ReviewRow.veterinarian_id == veterinarian_id)
            )
        ).one()
        average, count = row
        if average is None:
            return RatingSummary(average=None, count=0)
        return RatingSummary(average=Decimal(str(round(float(average), 2))), count=int(count))

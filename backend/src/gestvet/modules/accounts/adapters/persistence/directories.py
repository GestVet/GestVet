"""Adaptadores de lectores hacia tablas ajenas (`reviews`).

Consulta cruda, acotada a las preguntas de cada puerto y cubierta por
pruebas, igual que hacen los lectores de `appointments` hacia `pets` y
`availability`.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.accounts.ports.reviews_directory import RatingSummary


class SqlReviewsDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def summaries_for(self, veterinarian_ids: list[int]) -> dict[int, RatingSummary]:
        if not veterinarian_ids:
            return {}
        placeholders = ", ".join(f":id_{i}" for i in range(len(veterinarian_ids)))
        params = {f"id_{i}": value for i, value in enumerate(veterinarian_ids)}
        rows = await self._session.execute(
            text(
                "SELECT veterinarian_id, AVG(rating), COUNT(*) FROM reviews "
                f"WHERE veterinarian_id IN ({placeholders}) GROUP BY veterinarian_id"
            ),
            params,
        )
        return {
            int(veterinarian_id): RatingSummary(
                average=Decimal(str(round(float(average), 2))), count=int(count)
            )
            for veterinarian_id, average, count in rows.all()
        }

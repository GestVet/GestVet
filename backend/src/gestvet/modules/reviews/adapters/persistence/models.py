from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class ReviewRow(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("veterinarian_id", "client_id", name="uq_reviews_vet_client"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    veterinarian_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_reviews_veterinarian", ondelete="RESTRICT"), index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_reviews_client", ondelete="RESTRICT"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class AvailabilitySlotRow(Base):
    __tablename__ = "availability_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    veterinarian_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_slots_veterinarian", ondelete="CASCADE"), index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Toda consulta de agenda pregunta por un veterinario y un rango.
    __table_args__ = (Index("ix_slots_veterinarian_window", "veterinarian_id", "starts_at"),)

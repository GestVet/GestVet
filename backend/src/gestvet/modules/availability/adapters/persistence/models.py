from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base
from gestvet.modules.availability.domain.entities import ChangeRequestStatus, ShiftKind


class AvailabilitySlotRow(Base):
    __tablename__ = "availability_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    veterinarian_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_slots_veterinarian", ondelete="CASCADE"), index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    kind: Mapped[str] = mapped_column(String(16), default=ShiftKind.REGULAR.value)
    assigned_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_slots_assigned_by", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Toda consulta de agenda pregunta por un veterinario y un rango.
    __table_args__ = (Index("ix_slots_veterinarian_window", "veterinarian_id", "starts_at"),)


class ShiftChangeRequestRow(Base):
    __tablename__ = "shift_change_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    veterinarian_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_shift_change_requests_veterinarian", ondelete="CASCADE"),
        index=True,
    )
    # Si el turno se quita, el pedido queda como historia sin turno asociado.
    slot_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "availability_slots.id", name="fk_shift_change_requests_slot", ondelete="SET NULL"
        ),
        nullable=True,
    )
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(16), default=ChangeRequestStatus.PENDING.value, index=True
    )
    response: Mapped[str] = mapped_column(String(500), default="")
    resolved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_shift_change_requests_resolver", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

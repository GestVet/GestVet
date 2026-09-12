from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class PaymentRow(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", name="fk_payments_appointment", ondelete="RESTRICT"),
        index=True,
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_payments_client", ondelete="RESTRICT"), index=True
    )
    registered_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_payments_registered_by", ondelete="RESTRICT")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    method: Mapped[str] = mapped_column(String(20), index=True)
    reference: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(String(300), default="")
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    void_reason: Mapped[str] = mapped_column(String(300), default="")
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

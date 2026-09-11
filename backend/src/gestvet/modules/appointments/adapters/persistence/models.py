"""Modelo de persistencia de citas."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class AppointmentTypeRow(Base):
    __tablename__ = "appointment_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    # La duración se guarda en minutos y no como INTERVAL: es el único tipo que
    # SQLite y PostgreSQL entienden igual, y la base local de respaldo importa.
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AppointmentRow(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_appointments_client", ondelete="RESTRICT"), index=True
    )
    pet_id: Mapped[int] = mapped_column(
        ForeignKey("pets.id", name="fk_appointments_pet", ondelete="RESTRICT"), index=True
    )
    veterinarian_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_appointments_veterinarian", ondelete="RESTRICT"),
        index=True,
    )
    appointment_type_id: Mapped[int] = mapped_column(
        ForeignKey("appointment_types.id", name="fk_appointments_type", ondelete="RESTRICT")
    )
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), index=True)
    cancellation_reason: Mapped[str] = mapped_column(String(300), default="")
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_appointments_updated_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # La comprobación de solapamiento pregunta siempre por un veterinario y una
    # ventana de tiempo. Sin este índice recorre la tabla entera en cada alta.
    __table_args__ = (
        Index("ix_appointments_veterinarian_window", "veterinarian_id", "scheduled_at"),
    )

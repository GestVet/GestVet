from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class HospitalizationRow(Base):
    __tablename__ = "hospitalizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", name="fk_hospitalizations_appointment", ondelete="RESTRICT"),
        index=True,
    )
    pet_id: Mapped[int] = mapped_column(
        ForeignKey("pets.id", name="fk_hospitalizations_pet", ondelete="RESTRICT"), index=True
    )
    opened_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_hospitalizations_opened_by", ondelete="RESTRICT")
    )
    reason: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), index=True)
    discharge_notes: Mapped[str] = mapped_column(String(1000), default="")
    admitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    discharged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HospitalizationNoteRow(Base):
    __tablename__ = "hospitalization_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    hospitalization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "hospitalizations.id",
            name="fk_hospitalization_notes_hospitalization",
            ondelete="CASCADE",
        ),
        index=True,
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_hospitalization_notes_author", ondelete="RESTRICT")
    )
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

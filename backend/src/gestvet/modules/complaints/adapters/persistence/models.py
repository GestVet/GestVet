from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class ComplaintRow(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_complaints_client", ondelete="RESTRICT"), index=True
    )
    veterinarian_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_complaints_veterinarian", ondelete="RESTRICT"), index=True
    )
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", name="fk_complaints_appointment", ondelete="RESTRICT"),
        index=True,
    )
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ComplaintEvidenceRow(Base):
    __tablename__ = "complaint_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", name="fk_complaint_evidence_complaint", ondelete="CASCADE"),
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(150))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    storage_key: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_complaint_evidence_uploaded_by", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

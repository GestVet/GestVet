from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class ClinicalEntryRow(Base):
    __tablename__ = "clinical_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Las claves foráneas se declaran por nombre de tabla, sin importar el
    # modelo de `pets` ni el de `appointments`: eso sería una dependencia
    # entre módulos de dominio.
    pet_id: Mapped[int] = mapped_column(
        ForeignKey("pets.id", name="fk_clinical_entries_pet", ondelete="RESTRICT"), index=True
    )
    veterinarian_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_clinical_entries_veterinarian", ondelete="RESTRICT")
    )
    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id", name="fk_clinical_entries_appointment", ondelete="SET NULL"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(String(20))
    notes: Mapped[str] = mapped_column(Text)
    diagnosis: Mapped[str] = mapped_column(String(300), default="")
    treatment: Mapped[str] = mapped_column(String(300), default="")
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(precision=5, scale=2), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class AttachmentRow(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    # El adjunto no tiene sentido sin la entrada que lo posee: a diferencia de
    # `appointment_id` de arriba, acá se borra en cascada.
    clinical_entry_id: Mapped[int] = mapped_column(
        ForeignKey("clinical_entries.id", name="fk_attachments_clinical_entry", ondelete="CASCADE"),
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(150))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    storage_key: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_attachments_uploaded_by", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

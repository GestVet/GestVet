from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class ConsentTemplateRow(Base):
    __tablename__ = "consent_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Texto y no un tipo enumerado de la base: sumar un tipo de consentimiento
    # no tiene que obligar a una migración que altere la columna.
    kind: Mapped[str] = mapped_column(String(40), index=True)
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        UniqueConstraint("kind", "version", name="uq_consent_templates_kind_version"),
    )


class ConsentRow(Base):
    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("consent_templates.id", name="fk_consents_template", ondelete="RESTRICT"),
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(40))
    pet_id: Mapped[int] = mapped_column(
        ForeignKey("pets.id", name="fk_consents_pet", ondelete="RESTRICT"), index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_consents_client", ondelete="RESTRICT"), index=True
    )
    # Sin clave foránea a propósito: `appointments.risk_consent_id` ya apunta
    # hacia acá, y el ciclo entre las dos tablas obliga a crearlas y borrarlas
    # con restricciones diferidas. Nulo en la aceptación del riesgo de una
    # emergencia, que se firma antes de que exista la cita.
    appointment_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20))
    # Nulos mientras un pedido espera respuesta: el canal y la firma dependen
    # de cómo conteste el dueño.
    channel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    text_snapshot: Mapped[str] = mapped_column(Text)
    text_sha256: Mapped[str] = mapped_column(String(64))
    signer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    signer_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_consents_signer_user", ondelete="SET NULL"),
        nullable=True,
    )
    witness_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_consents_witness", ondelete="SET NULL"), nullable=True
    )
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_consents_requested_by", ondelete="SET NULL"),
        nullable=True,
    )
    details: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str] = mapped_column(String(45), default="")
    user_agent: Mapped[str] = mapped_column(String(300), default="")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

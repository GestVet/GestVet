"""Modelo de persistencia de mascotas. Es una tabla, no una entidad."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class PetRow(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    species: Mapped[str] = mapped_column(String(40), index=True)
    breed: Mapped[str] = mapped_column(String(60))
    birth_date: Mapped[date] = mapped_column(Date)
    # La clave foránea se declara por nombre de tabla, sin importar el modelo
    # de `accounts`: eso seria una dependencia entre modulos de dominio.
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_pets_owner", ondelete="RESTRICT"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

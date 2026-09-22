from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80), default="")
    last_name: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(32), default="")
    document_id: Mapped[str] = mapped_column(String(8), default="")
    role: Mapped[str] = mapped_column(String(32), index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class PasswordResetTokenRow(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_password_reset_tokens_user", ondelete="RESTRICT"),
        index=True,
    )
    # SHA-256 en hexadecimal: 64 caracteres fijos. Nunca se guarda el token en
    # claro, igual que una contraseña.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class SpecialtyRow(Base):
    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    # El nombre sin tildes ni mayúsculas: lo que impide cargar dos veces lo mismo.
    name_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str] = mapped_column(String(240), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class VeterinarianSpecialtyRow(Base):
    __tablename__ = "veterinarian_specialties"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_veterinarian_specialties_user", ondelete="CASCADE"),
        primary_key=True,
    )
    specialty_id: Mapped[int] = mapped_column(
        ForeignKey(
            "specialties.id", name="fk_veterinarian_specialties_specialty", ondelete="RESTRICT"
        ),
        primary_key=True,
    )


class UserLayoutPreferenceRow(Base):
    __tablename__ = "user_layout_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_user_layout_preferences_user", ondelete="CASCADE"),
        primary_key=True,
    )
    sidebar_order: Mapped[list[str]] = mapped_column(JSON, default=list)
    dashboard_blocks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

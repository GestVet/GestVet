from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from gestvet.core.database import Base


class AccessRoleRow(Base):
    __tablename__ = "access_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(200), default="")
    account_kind: Mapped[str] = mapped_column(String(32), index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class AccessRolePermissionRow(Base):
    __tablename__ = "access_role_permissions"

    role_id: Mapped[int] = mapped_column(
        ForeignKey("access_roles.id", name="fk_access_role_permissions_role", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    permission: Mapped[str] = mapped_column(String(64), primary_key=True)


class UserAccessRoleRow(Base):
    """El rol asignado a una cuenta. Sin fila, la cuenta usa el de sistema de su tipo."""

    __tablename__ = "user_access_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_user_access_roles_user", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("access_roles.id", name="fk_user_access_roles_role", ondelete="RESTRICT"),
        index=True,
    )

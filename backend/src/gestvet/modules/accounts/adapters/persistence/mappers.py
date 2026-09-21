"""Traducción entre la fila de la tabla y la entidad de dominio.

Este archivo es la razón por la que el dominio puede ignorar SQLAlchemy.
"""

from __future__ import annotations

from datetime import UTC, datetime

from gestvet.core.timestamps import as_utc
from gestvet.modules.accounts.adapters.persistence.models import (
    PasswordResetTokenRow,
    UserLayoutPreferenceRow,
    UserRow,
)
from gestvet.modules.accounts.domain.entities import (
    DashboardBlockPreference,
    LayoutPreferences,
    PasswordResetToken,
    Role,
    User,
    UserLayoutPreference,
)


def row_to_entity(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        first_name=row.first_name,
        last_name=row.last_name,
        phone=row.phone,
        document_id=row.document_id,
        role=Role(row.role),
        password_hash=row.password_hash,
        is_active=row.is_active,
        created_at=as_utc(row.created_at),
    )


def entity_to_row(user: User) -> UserRow:
    return UserRow(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        document_id=user.document_id,
        role=user.role.value,
        password_hash=user.password_hash,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def reset_token_row_to_entity(row: PasswordResetTokenRow) -> PasswordResetToken:
    return PasswordResetToken(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=as_utc(row.expires_at),
        used_at=as_utc(row.used_at) if row.used_at else None,
        created_at=as_utc(row.created_at),
    )


def reset_token_entity_to_row(token: PasswordResetToken) -> PasswordResetTokenRow:
    return PasswordResetTokenRow(
        user_id=token.user_id,
        token_hash=token.token_hash,
        expires_at=token.expires_at,
        used_at=token.used_at,
        created_at=token.created_at,
    )


def layout_row_to_entity(row: UserLayoutPreferenceRow) -> UserLayoutPreference:
    blocks = tuple(
        DashboardBlockPreference(
            id=str(b.get("id", "")),
            visible=bool(b.get("visible", True)),
        )
        for b in (row.dashboard_blocks or [])
    )
    prefs = LayoutPreferences(
        sidebar_order=tuple(row.sidebar_order or []),
        dashboard_blocks=blocks,
        updated_at=as_utc(row.updated_at),
    )
    return UserLayoutPreference(user_id=row.user_id, preferences=prefs)


def layout_entity_to_row(layout: UserLayoutPreference) -> UserLayoutPreferenceRow:
    return UserLayoutPreferenceRow(
        user_id=layout.user_id,
        sidebar_order=list(layout.sidebar_order),
        dashboard_blocks=[{"id": b.id, "visible": b.visible} for b in layout.dashboard_blocks],
        updated_at=layout.updated_at or datetime.now(UTC),
    )

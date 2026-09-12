"""Traducción entre la fila de la tabla y la entidad de dominio.

Este archivo es la razón por la que el dominio puede ignorar SQLAlchemy.
"""

from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.accounts.adapters.persistence.models import PasswordResetTokenRow, UserRow
from gestvet.modules.accounts.domain.entities import PasswordResetToken, Role, User


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
        can_cover_emergencies=row.can_cover_emergencies,
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
        can_cover_emergencies=user.can_cover_emergencies,
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

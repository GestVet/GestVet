"""Traducción entre la fila de la tabla y la entidad de dominio.

Este archivo es la razón por la que el dominio puede ignorar SQLAlchemy.
"""

from __future__ import annotations

from gestvet.accounts.adapters.persistence.models import UserRow
from gestvet.accounts.domain.entities import Role, User


def row_to_entity(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        first_name=row.first_name,
        last_name=row.last_name,
        phone=row.phone,
        role=Role(row.role),
        password_hash=row.password_hash,
        is_active=row.is_active,
        created_at=row.created_at,
    )


def entity_to_row(user: User) -> UserRow:
    return UserRow(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        role=user.role.value,
        password_hash=user.password_hash,
        is_active=user.is_active,
        created_at=user.created_at,
    )

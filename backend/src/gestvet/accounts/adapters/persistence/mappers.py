"""Traducción entre la fila de la tabla y la entidad de dominio.

Este archivo es la razón por la que el dominio puede ignorar SQLAlchemy.
"""

from __future__ import annotations

from datetime import UTC, datetime

from gestvet.accounts.adapters.persistence.models import UserRow
from gestvet.accounts.domain.entities import Role, User


def _as_utc(moment: datetime) -> datetime:
    """Devuelve la fecha con su zona horaria puesta.

    SQLite no almacena la zona, asi que una fecha guardada con `UTC` vuelve
    ingenua. Sin esta correccion el API serializa la marca sin desplazamiento y
    el navegador la interpreta como hora local: la fecha se corre tantas horas
    como diga el reloj de quien mira. Y solo pasa en local, porque PostgreSQL
    si conserva la zona, que es la forma mas cara de encontrar el error.
    """
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


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
        created_at=_as_utc(row.created_at),
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

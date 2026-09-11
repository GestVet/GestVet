"""Traducción entre la fila de la tabla y la entidad de dominio."""

from __future__ import annotations

from datetime import UTC, datetime

from gestvet.pets.adapters.persistence.models import PetRow
from gestvet.pets.domain.entities import Pet


def _as_utc(moment: datetime) -> datetime:
    """SQLite no guarda la zona horaria; se repone al leer."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def row_to_entity(row: PetRow) -> Pet:
    return Pet(
        id=row.id,
        name=row.name,
        species=row.species,
        breed=row.breed,
        birth_date=row.birth_date,
        owner_id=row.owner_id,
        is_active=row.is_active,
        created_at=_as_utc(row.created_at),
    )


def entity_to_row(pet: Pet) -> PetRow:
    return PetRow(
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        birth_date=pet.birth_date,
        owner_id=pet.owner_id,
        is_active=pet.is_active,
        created_at=pet.created_at,
    )

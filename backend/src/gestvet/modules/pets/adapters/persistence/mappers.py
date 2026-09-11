from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.pets.adapters.persistence.models import PetRow
from gestvet.modules.pets.domain.entities import Pet


def row_to_entity(row: PetRow) -> Pet:
    return Pet(
        id=row.id,
        name=row.name,
        species=row.species,
        breed=row.breed,
        birth_date=row.birth_date,
        owner_id=row.owner_id,
        is_active=row.is_active,
        created_at=as_utc(row.created_at),
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

from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.pets.adapters.persistence.models import PetRow
from gestvet.modules.pets.domain.entities import Pet, PetSex


def row_to_entity(row: PetRow) -> Pet:
    return Pet(
        id=row.id,
        name=row.name,
        species=row.species,
        breed=row.breed,
        birth_date=row.birth_date,
        owner_id=row.owner_id,
        is_active=row.is_active,
        sex=PetSex(row.sex) if row.sex is not None else None,
        color=row.color,
        microchip_number=row.microchip_number,
        temperament=row.temperament,
        weight_kg=row.weight_kg,
        height_cm=row.height_cm,
        is_sterilized=row.is_sterilized,
        allergies=row.allergies,
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
        sex=pet.sex.value if pet.sex is not None else None,
        color=pet.color,
        microchip_number=pet.microchip_number,
        temperament=pet.temperament,
        weight_kg=pet.weight_kg,
        height_cm=pet.height_cm,
        is_sterilized=pet.is_sterilized,
        allergies=pet.allergies,
        created_at=pet.created_at,
    )

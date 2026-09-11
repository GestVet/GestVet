"""Contrato HTTP del módulo de mascotas.

El alta no acepta `owner_id`: el servidor lo toma de la credencial. Es la misma
regla que impide pedir un rol al registrarse.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from gestvet.pets.domain.entities import (
    MAX_BREED_LENGTH,
    MAX_NAME_LENGTH,
    MAX_SPECIES_LENGTH,
    Pet,
)


class RegisterPetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    species: str = Field(min_length=1, max_length=MAX_SPECIES_LENGTH)
    breed: str = Field(min_length=1, max_length=MAX_BREED_LENGTH)
    birth_date: date


class ChangePetStatusRequest(BaseModel):
    is_active: bool


class PetResponse(BaseModel):
    id: int
    name: str
    species: str
    breed: str
    birth_date: date
    age_in_years: int
    owner_id: int
    is_active: bool
    created_at: datetime

    @classmethod
    def from_entity(cls, pet: Pet) -> PetResponse:
        return cls(
            id=pet.id or 0,
            name=pet.name,
            species=pet.species,
            breed=pet.breed,
            birth_date=pet.birth_date,
            age_in_years=pet.age_in_years(),
            owner_id=pet.owner_id,
            is_active=pet.is_active,
            created_at=pet.created_at,
        )


class PetPageResponse(BaseModel):
    items: list[PetResponse]
    total: int

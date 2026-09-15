"""Contrato HTTP del módulo de mascotas.

El alta no acepta `owner_id`: el servidor lo toma de la credencial. Es la misma
regla que impide pedir un rol al registrarse.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from gestvet.modules.pets.domain.entities import (
    MAX_ALLERGIES_LENGTH,
    MAX_BREED_LENGTH,
    MAX_COLOR_LENGTH,
    MAX_MICROCHIP_LENGTH,
    MAX_NAME_LENGTH,
    MAX_SPECIES_LENGTH,
    MAX_TEMPERAMENT_LENGTH,
    Pet,
    PetSex,
)


class RegisterPetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    species: str = Field(min_length=1, max_length=MAX_SPECIES_LENGTH)
    breed: str = Field(min_length=1, max_length=MAX_BREED_LENGTH)
    birth_date: date


class RegisterPetForOwnerRequest(BaseModel):
    """Lo mínimo para una mascota dada de alta por el personal en una emergencia.

    No hay tiempo de preguntar raza ni fecha de nacimiento: esos datos quedan
    con un valor provisorio y el dueño los completa después desde su propia
    ficha, igual que cualquier otra mascota.
    """

    owner_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    species: str = Field(min_length=1, max_length=MAX_SPECIES_LENGTH)


class ChangePetStatusRequest(BaseModel):
    is_active: bool


class CorrectPetStatusRequest(BaseModel):
    is_active: bool
    reason: str = Field(min_length=1, max_length=300)


class UpdatePetOwnerProfileRequest(BaseModel):
    sex: PetSex | None = None
    color: str = Field(default="", max_length=MAX_COLOR_LENGTH)
    microchip_number: str = Field(default="", max_length=MAX_MICROCHIP_LENGTH)
    temperament: str = Field(default="", max_length=MAX_TEMPERAMENT_LENGTH)
    # Sin estos tres, la ficha conserva lo que tenía.
    species: str | None = Field(default=None, min_length=1, max_length=MAX_SPECIES_LENGTH)
    breed: str | None = Field(default=None, min_length=1, max_length=MAX_BREED_LENGTH)
    birth_date: date | None = None
    # El dueño los conoce de memoria; el veterinario igual puede confirmarlos
    # o corregirlos en consulta desde `UpdatePetClinicalProfileRequest`.
    weight_kg: Decimal | None = Field(default=None, gt=0)
    height_cm: Decimal | None = Field(default=None, gt=0)
    is_sterilized: bool | None = None
    allergies: str = Field(default="", max_length=MAX_ALLERGIES_LENGTH)


class UpdatePetClinicalProfileRequest(BaseModel):
    # Sin fecha, se conserva la que tenía: la corrige el veterinario si en la
    # emergencia quedó provisoria.
    birth_date: date | None = None
    weight_kg: Decimal | None = Field(default=None, gt=0)
    height_cm: Decimal | None = Field(default=None, gt=0)
    is_sterilized: bool | None = None
    allergies: str = Field(default="", max_length=MAX_ALLERGIES_LENGTH)


class PetResponse(BaseModel):
    id: int
    name: str
    species: str
    breed: str
    birth_date: date
    age_in_years: int
    owner_id: int
    is_active: bool
    sex: PetSex | None
    color: str
    microchip_number: str
    temperament: str
    weight_kg: Decimal | None
    height_cm: Decimal | None
    is_sterilized: bool | None
    allergies: str
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
            sex=pet.sex,
            color=pet.color,
            microchip_number=pet.microchip_number,
            temperament=pet.temperament,
            weight_kg=pet.weight_kg,
            height_cm=pet.height_cm,
            is_sterilized=pet.is_sterilized,
            allergies=pet.allergies,
            created_at=pet.created_at,
        )


class PetPageResponse(BaseModel):
    items: list[PetResponse]
    total: int

"""Caso de uso: actualizar los datos de la mascota que conoce el dueño.

Sexo, color, microchip y temperamento no se miden en consulta: los sabe quien
convive con la mascota. Los datos clínicos (peso, altura, esterilización,
alergias) los actualiza el veterinario por `UpdatePetClinicalProfile`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.pets.domain.catalog import ensure_in_catalog
from gestvet.modules.pets.domain.entities import Pet, PetSex
from gestvet.modules.pets.domain.exceptions import PetNotFound
from gestvet.modules.pets.ports.pet_repository import PetRepository


@dataclass(frozen=True, slots=True)
class UpdatePetOwnerProfileCommand:
    pet_id: int
    owner_id: int
    sex: PetSex | None
    color: str
    microchip_number: str
    temperament: str
    species: str | None = None
    breed: str | None = None
    birth_date: date | None = None


class UpdatePetOwnerProfile:
    def __init__(self, pets: PetRepository, activity: ActivityRecorder) -> None:
        self._pets = pets
        self._activity = activity

    async def __call__(self, command: UpdatePetOwnerProfileCommand) -> Pet:
        pet = await self._pets.get(command.pet_id, owner_id=command.owner_id)
        if pet is None:
            raise PetNotFound(command.pet_id)

        if command.species is not None or command.breed is not None:
            ensure_in_catalog(command.species or pet.species, command.breed or pet.breed)

        pet.update_owner_profile(
            sex=command.sex,
            color=command.color,
            microchip_number=command.microchip_number,
            temperament=command.temperament,
            species=command.species,
            breed=command.breed,
            birth_date=command.birth_date,
        )
        guardada = await self._pets.save(pet)
        await self._activity.record(
            command.owner_id, ActivityKind.PET_PROFILE_UPDATED, guardada.name
        )
        return guardada

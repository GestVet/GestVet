"""Caso de uso: actualizar los datos de la mascota que conoce el dueño.

Especie, raza, nacimiento, sexo, color, microchip y temperamento no se miden en
consulta: los sabe quien convive con la mascota. Los datos clínicos (peso, altura, esterilización,
alergias) los actualiza el veterinario por `UpdatePetClinicalProfile`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.pets.domain.entities import Pet, PetSex
from gestvet.modules.pets.domain.exceptions import PetNotFound
from gestvet.modules.pets.ports.catalog_repository import PetCatalogRepository
from gestvet.modules.pets.ports.pet_repository import PetRepository
from gestvet.modules.pets.use_cases.manage_catalog import ensure_offered


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
    def __init__(
        self, pets: PetRepository, catalog: PetCatalogRepository, activity: ActivityRecorder
    ) -> None:
        self._pets = pets
        self._catalog = catalog
        self._activity = activity

    async def __call__(self, command: UpdatePetOwnerProfileCommand) -> Pet:
        pet = await self._pets.get(command.pet_id, owner_id=command.owner_id)
        if pet is None:
            raise PetNotFound(command.pet_id)

        species = command.species or pet.species
        breed = command.breed or pet.breed
        # Solo se valida lo que cambia: una raza que la clínica desactivó no
        # impide corregir el color de una mascota que ya la tenía.
        if (species, breed) != (pet.species, pet.breed):
            await ensure_offered(self._catalog, species, breed)

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

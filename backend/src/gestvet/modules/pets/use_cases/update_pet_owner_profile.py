"""Caso de uso: actualizar los datos de la mascota que conoce el dueño.

Sexo, color, microchip y temperamento no se miden en consulta: los sabe quien
convive con la mascota. Los datos clínicos (peso, altura, esterilización,
alergias) los actualiza el veterinario por `UpdatePetClinicalProfile`.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.pets.domain.entities import Pet, PetSex
from gestvet.modules.pets.domain.exceptions import PetNotFound
from gestvet.modules.pets.ports.pet_repository import PetRepository


@dataclass(frozen=True, slots=True)
class UpdatePetOwnerProfileCommand:
    pet_id: int
    owner_id: int
    breed: str
    sex: PetSex | None
    color: str
    microchip_number: str
    temperament: str


class UpdatePetOwnerProfile:
    def __init__(self, pets: PetRepository, activity: ActivityRecorder) -> None:
        self._pets = pets
        self._activity = activity

    async def __call__(self, command: UpdatePetOwnerProfileCommand) -> Pet:
        pet = await self._pets.get(command.pet_id, owner_id=command.owner_id)
        if pet is None:
            raise PetNotFound(command.pet_id)

        pet.update_owner_profile(
            breed=command.breed,
            sex=command.sex,
            color=command.color,
            microchip_number=command.microchip_number,
            temperament=command.temperament,
        )
        guardada = await self._pets.save(pet)
        await self._activity.record(
            command.owner_id, ActivityKind.PET_PROFILE_UPDATED, guardada.name
        )
        return guardada

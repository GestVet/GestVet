"""Caso de uso: actualizar los datos clínicos de la mascota.

Peso, altura, esterilización y alergias los confirma el veterinario en
consulta, no el dueño. Es el mismo criterio que ya rige `AddClinicalEntry`:
cargar un dato clínico es un acto clínico.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.pets.domain.entities import Pet
from gestvet.modules.pets.domain.exceptions import PetNotFound
from gestvet.modules.pets.ports.pet_repository import PetRepository


@dataclass(frozen=True, slots=True)
class UpdatePetClinicalProfileCommand:
    pet_id: int
    updated_by: int
    birth_date: date
    weight_kg: Decimal | None
    height_cm: Decimal | None
    is_sterilized: bool | None
    allergies: str


class UpdatePetClinicalProfile:
    def __init__(self, pets: PetRepository, activity: ActivityRecorder) -> None:
        self._pets = pets
        self._activity = activity

    async def __call__(self, command: UpdatePetClinicalProfileCommand) -> Pet:
        pet = await self._pets.get(command.pet_id)
        if pet is None:
            raise PetNotFound(command.pet_id)

        pet.update_clinical_profile(
            birth_date=command.birth_date,
            weight_kg=command.weight_kg,
            height_cm=command.height_cm,
            is_sterilized=command.is_sterilized,
            allergies=command.allergies,
        )
        guardada = await self._pets.save(pet)
        await self._activity.record(
            command.updated_by, ActivityKind.PET_CLINICAL_PROFILE_UPDATED, guardada.name
        )
        return guardada

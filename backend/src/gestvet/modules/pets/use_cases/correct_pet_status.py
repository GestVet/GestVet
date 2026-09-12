"""Caso de uso: corregir el estado de una mascota.

Distinto de `ChangePetStatus`: ese lo usa el dueño y solo avanza hacia
"fallecida". Este lo usa el personal de la clínica para deshacer un error de
carga, exige un motivo y deja su propio asiento en la bitácora.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.pets.domain.entities import Pet
from gestvet.modules.pets.domain.exceptions import InvalidPetData, PetNotFound
from gestvet.modules.pets.ports.pet_repository import PetRepository

MAX_REASON_LENGTH = 300


@dataclass(frozen=True, slots=True)
class CorrectPetStatusCommand:
    pet_id: int
    actor_id: int
    is_active: bool
    reason: str


class CorrectPetStatus:
    def __init__(self, pets: PetRepository, activity: ActivityRecorder) -> None:
        self._pets = pets
        self._activity = activity

    async def __call__(self, command: CorrectPetStatusCommand) -> Pet:
        reason = command.reason.strip()
        if not reason:
            raise InvalidPetData("La corrección exige indicar el motivo.")
        if len(reason) > MAX_REASON_LENGTH:
            raise InvalidPetData(f"El motivo admite {MAX_REASON_LENGTH} caracteres como máximo.")

        # Sin acotar por dueño: quien corrige es personal de la clínica, no el
        # dueño de la mascota.
        pet = await self._pets.get(command.pet_id)
        if pet is None:
            raise PetNotFound(command.pet_id)

        if command.is_active:
            pet.activate()
        else:
            pet.deactivate()

        guardada = await self._pets.save(pet)
        await self._activity.record(
            command.actor_id,
            ActivityKind.PET_STATUS_CORRECTED,
            f"{guardada.name}: {reason}",
        )
        return guardada

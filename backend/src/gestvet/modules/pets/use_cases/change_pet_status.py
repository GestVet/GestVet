"""Caso de uso: dar de baja o reactivar una mascota.

El original borraba con un cambio de estado y no con un DELETE, que es lo
correcto: una mascota con historial de citas no se puede hacer desaparecer sin
romper ese historial.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.pets.domain.entities import Pet
from gestvet.modules.pets.domain.exceptions import PetNotFound, PetStatusIsFinal
from gestvet.modules.pets.ports.pet_repository import PetRepository


@dataclass(frozen=True, slots=True)
class ChangePetStatusCommand:
    pet_id: int
    owner_id: int
    is_active: bool


class ChangePetStatus:
    """Dar de baja una mascota propia: que falleció, y es de un solo sentido.

    El dueño puede pasarla de viva a fallecida, nunca al revés. Revertir un
    error de carga es competencia del personal de la clínica, que lo hace por
    `CorrectPetStatus` con un motivo obligatorio y su propio asiento.
    """

    def __init__(self, pets: PetRepository, activity: ActivityRecorder) -> None:
        self._pets = pets
        self._activity = activity

    async def __call__(self, command: ChangePetStatusCommand) -> Pet:
        # Se acota por dueño en la propia consulta. Si la mascota es de otro,
        # el resultado es "no existe" y no "no puedes": responder distinto
        # confirmaría que ese identificador pertenece a alguien.
        pet = await self._pets.get(command.pet_id, owner_id=command.owner_id)
        if pet is None:
            raise PetNotFound(command.pet_id)

        if not pet.is_active:
            raise PetStatusIsFinal(pet.id or command.pet_id)

        if not command.is_active:
            pet.deactivate()
            guardada = await self._pets.save(pet)
            await self._activity.record(
                command.owner_id,
                ActivityKind.PET_STATUS_CHANGED,
                f"{guardada.name}: dada de baja",
            )
            return guardada

        return pet

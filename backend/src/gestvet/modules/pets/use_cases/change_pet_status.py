"""Caso de uso: dar de baja o reactivar una mascota.

El original borraba con un cambio de estado y no con un DELETE, que es lo
correcto: una mascota con historial de citas no se puede hacer desaparecer sin
romper ese historial.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.modules.pets.domain.entities import Pet
from gestvet.modules.pets.domain.exceptions import PetNotFound
from gestvet.modules.pets.ports.pet_repository import PetRepository


@dataclass(frozen=True, slots=True)
class ChangePetStatusCommand:
    pet_id: int
    owner_id: int
    is_active: bool


class ChangePetStatus:
    def __init__(self, pets: PetRepository) -> None:
        self._pets = pets

    async def __call__(self, command: ChangePetStatusCommand) -> Pet:
        # Se acota por dueño en la propia consulta. Si la mascota es de otro,
        # el resultado es "no existe" y no "no podés": responder distinto
        # confirmaría que ese identificador pertenece a alguien.
        pet = await self._pets.get(command.pet_id, owner_id=command.owner_id)
        if pet is None:
            raise PetNotFound(command.pet_id)

        if command.is_active:
            pet.activate()
        else:
            pet.deactivate()
        return await self._pets.save(pet)

"""Caso de uso: alta de una mascota."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from gestvet.pets.domain.entities import Pet
from gestvet.pets.ports.pet_repository import PetRepository


@dataclass(frozen=True, slots=True)
class RegisterPetCommand:
    name: str
    species: str
    breed: str
    birth_date: date
    owner_id: int


class RegisterPet:
    def __init__(self, pets: PetRepository) -> None:
        self._pets = pets

    async def __call__(self, command: RegisterPetCommand) -> Pet:
        # El dueño lo fija el servidor a partir de la credencial, nunca el
        # cuerpo de la petición. Es la misma regla que protege al rol.
        pet = Pet(
            name=command.name,
            species=command.species,
            breed=command.breed,
            birth_date=command.birth_date,
            owner_id=command.owner_id,
        )
        return await self._pets.add(pet)

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.pets.domain.entities import Pet
from gestvet.modules.pets.ports.catalog_repository import PetCatalogRepository
from gestvet.modules.pets.ports.pet_repository import PetRepository
from gestvet.modules.pets.use_cases.manage_catalog import ensure_offered


@dataclass(frozen=True, slots=True)
class RegisterPetCommand:
    name: str
    species: str
    breed: str
    birth_date: date
    owner_id: int


class RegisterPet:
    def __init__(
        self, pets: PetRepository, catalog: PetCatalogRepository, activity: ActivityRecorder
    ) -> None:
        self._pets = pets
        self._catalog = catalog
        self._activity = activity

    async def __call__(self, command: RegisterPetCommand) -> Pet:
        # Especie y raza salen del catálogo: el texto libre partía una misma
        # especie en varias escrituras.
        await ensure_offered(self._catalog, command.species, command.breed)

        # El dueño lo fija el servidor a partir de la credencial, nunca el
        # cuerpo de la petición. Es la misma regla que protege al rol.
        pet = Pet(
            name=command.name,
            species=command.species,
            breed=command.breed,
            birth_date=command.birth_date,
            owner_id=command.owner_id,
        )
        creada = await self._pets.add(pet)
        await self._activity.record(command.owner_id, ActivityKind.PET_REGISTERED, creada.name)
        return creada

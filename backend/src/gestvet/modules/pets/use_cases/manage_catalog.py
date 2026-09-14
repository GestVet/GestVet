"""Casos de uso: consultar y ampliar el catálogo de especies y razas.

Cuando llega un animal que no está en la lista, la administración lo agrega en
el momento. Cada nombre se formatea antes de guardarse y se compara sin tildes
ni mayúsculas, así "pastor aleman" no entra como otra raza al lado de "Pastor
alemán". Corregir un nombre lo corrige también en las fichas que lo usan.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.modules.pets.domain.catalog import (
    UNKNOWN_BREED,
    Breed,
    Species,
    catalog_key,
    format_breed_name,
    format_species_name,
)
from gestvet.modules.pets.domain.exceptions import (
    CatalogEntryNotFound,
    CatalogNameTaken,
    InvalidPetData,
)
from gestvet.modules.pets.ports.catalog_repository import PetCatalogRepository


async def ensure_offered(catalog: PetCatalogRepository, species: str, breed: str) -> None:
    """La especie y la raza son de las que el catálogo ofrece hoy."""
    breeds = await catalog.offered_breeds(species.strip())
    if breeds is None:
        raise InvalidPetData("Elige una especie de la lista.")
    if breed.strip() not in breeds:
        raise InvalidPetData(f"Elige una raza de la lista para {species.strip()}.")


async def _require_species(catalog: PetCatalogRepository, species_id: int) -> Species:
    species = await catalog.get_species(species_id)
    if species is None:
        raise CatalogEntryNotFound("especie", species_id)
    return species


async def _ensure_species_name_free(
    catalog: PetCatalogRepository, name: str, own_id: int | None
) -> None:
    found = await catalog.find_species_id(catalog_key(name))
    if found is not None and found != own_id:
        raise CatalogNameTaken(name)


async def _ensure_breed_name_free(
    catalog: PetCatalogRepository, species_id: int, name: str, own_id: int | None
) -> None:
    found = await catalog.find_breed_id(species_id, catalog_key(name))
    if found is not None and found != own_id:
        raise CatalogNameTaken(name)


class AddSpecies:
    def __init__(self, catalog: PetCatalogRepository) -> None:
        self._catalog = catalog

    async def __call__(self, raw_name: str) -> Species:
        name = format_species_name(raw_name)
        await _ensure_species_name_free(self._catalog, name, None)
        species = await self._catalog.add_species(Species(name=name))
        # Toda especie ofrece "Sin especificar" desde el primer momento: sin
        # esa raza no se podría dar de alta a la mascota en una emergencia.
        unknown = await self._catalog.add_breed(
            Breed(name=UNKNOWN_BREED, species_id=species.id or 0)
        )
        species.breeds = [unknown]
        return species


@dataclass(frozen=True, slots=True)
class UpdateCatalogEntryCommand:
    entry_id: int
    name: str
    is_active: bool


class UpdateSpecies:
    def __init__(self, catalog: PetCatalogRepository) -> None:
        self._catalog = catalog

    async def __call__(self, command: UpdateCatalogEntryCommand) -> Species:
        species = await _require_species(self._catalog, command.entry_id)
        previous = species.name
        name = format_species_name(command.name)
        await _ensure_species_name_free(self._catalog, name, species.id)
        species.update(name=name, is_active=command.is_active)
        saved = await self._catalog.save_species(species)
        if name != previous:
            await self._catalog.rename_species_in_pets(previous, name)
        return saved


@dataclass(frozen=True, slots=True)
class AddBreedCommand:
    species_id: int
    name: str


class AddBreed:
    def __init__(self, catalog: PetCatalogRepository) -> None:
        self._catalog = catalog

    async def __call__(self, command: AddBreedCommand) -> Breed:
        species = await _require_species(self._catalog, command.species_id)
        name = format_breed_name(command.name)
        await _ensure_breed_name_free(self._catalog, command.species_id, name, None)
        return await self._catalog.add_breed(Breed(name=name, species_id=species.id or 0))


class UpdateBreed:
    def __init__(self, catalog: PetCatalogRepository) -> None:
        self._catalog = catalog

    async def __call__(self, command: UpdateCatalogEntryCommand) -> Breed:
        breed = await self._catalog.get_breed(command.entry_id)
        if breed is None:
            raise CatalogEntryNotFound("raza", command.entry_id)
        previous = breed.name
        name = format_breed_name(command.name)
        await _ensure_breed_name_free(self._catalog, breed.species_id, name, breed.id)
        breed.update(name=name, is_active=command.is_active)
        saved = await self._catalog.save_breed(breed)
        if name != previous:
            species = await _require_species(self._catalog, breed.species_id)
            await self._catalog.rename_breed_in_pets(species.name, previous, name)
        return saved

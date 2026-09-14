from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.modules.pets.adapters.persistence.models import PetBreedRow, PetRow, PetSpeciesRow
from gestvet.modules.pets.domain.catalog import Breed, Species, breed_sort_key, catalog_key


def _species(row: PetSpeciesRow, breeds: list[Breed] | None = None) -> Species:
    return Species(
        id=row.id,
        name=row.name,
        is_active=row.is_active,
        sort_order=row.sort_order,
        breeds=breeds or [],
    )


def _breed(row: PetBreedRow) -> Breed:
    return Breed(id=row.id, name=row.name, species_id=row.species_id, is_active=row.is_active)


class SqlAlchemyPetCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_species(self, *, include_inactive: bool) -> list[Species]:
        species_query = select(PetSpeciesRow).order_by(
            PetSpeciesRow.sort_order, PetSpeciesRow.name_key
        )
        breeds_query = select(PetBreedRow)
        if not include_inactive:
            species_query = species_query.where(PetSpeciesRow.is_active.is_(True))
            breeds_query = breeds_query.where(PetBreedRow.is_active.is_(True))
        species_rows = (await self._session.execute(species_query)).scalars().all()
        by_species: dict[int, list[Breed]] = {}
        for row in (await self._session.execute(breeds_query)).scalars():
            by_species.setdefault(row.species_id, []).append(_breed(row))
        return [
            _species(row, sorted(by_species.get(row.id, []), key=lambda b: breed_sort_key(b.name)))
            for row in species_rows
        ]

    async def offered_breeds(self, species: str) -> frozenset[str] | None:
        species_id = (
            await self._session.execute(
                select(PetSpeciesRow.id).where(
                    PetSpeciesRow.name == species, PetSpeciesRow.is_active.is_(True)
                )
            )
        ).scalar_one_or_none()
        if species_id is None:
            return None
        names = await self._session.execute(
            select(PetBreedRow.name).where(
                PetBreedRow.species_id == species_id, PetBreedRow.is_active.is_(True)
            )
        )
        return frozenset(names.scalars())

    async def get_species(self, species_id: int) -> Species | None:
        row = await self._session.get(PetSpeciesRow, species_id)
        return _species(row) if row else None

    async def get_breed(self, breed_id: int) -> Breed | None:
        row = await self._session.get(PetBreedRow, breed_id)
        return _breed(row) if row else None

    async def find_species_id(self, key: str) -> int | None:
        statement = select(PetSpeciesRow.id).where(PetSpeciesRow.name_key == key)
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def find_breed_id(self, species_id: int, key: str) -> int | None:
        statement = select(PetBreedRow.id).where(
            PetBreedRow.species_id == species_id, PetBreedRow.name_key == key
        )
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def add_species(self, species: Species) -> Species:
        row = PetSpeciesRow(
            name=species.name,
            name_key=catalog_key(species.name),
            sort_order=species.sort_order,
            is_active=species.is_active,
        )
        self._session.add(row)
        await self._session.flush()
        return _species(row)

    async def add_breed(self, breed: Breed) -> Breed:
        row = PetBreedRow(
            species_id=breed.species_id,
            name=breed.name,
            name_key=catalog_key(breed.name),
            is_active=breed.is_active,
        )
        self._session.add(row)
        await self._session.flush()
        return _breed(row)

    async def save_species(self, species: Species) -> Species:
        row = await self._session.get(PetSpeciesRow, species.id)
        if row is None:
            raise ValueError(f"La especie {species.id} ya no existe.")
        row.name = species.name
        row.name_key = catalog_key(species.name)
        row.is_active = species.is_active
        await self._session.flush()
        return _species(row)

    async def save_breed(self, breed: Breed) -> Breed:
        row = await self._session.get(PetBreedRow, breed.id)
        if row is None:
            raise ValueError(f"La raza {breed.id} ya no existe.")
        row.name = breed.name
        row.name_key = catalog_key(breed.name)
        row.is_active = breed.is_active
        await self._session.flush()
        return _breed(row)

    async def rename_species_in_pets(self, old: str, new: str) -> None:
        await self._session.execute(update(PetRow).where(PetRow.species == old).values(species=new))

    async def rename_breed_in_pets(self, species: str, old: str, new: str) -> None:
        await self._session.execute(
            update(PetRow).where(PetRow.species == species, PetRow.breed == old).values(breed=new)
        )

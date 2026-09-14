from __future__ import annotations

from pydantic import BaseModel, Field

from gestvet.modules.pets.domain.catalog import Breed, Species
from gestvet.modules.pets.domain.entities import MAX_BREED_LENGTH


class SpeciesResponse(BaseModel):
    name: str
    breeds: list[str]


class PetCatalogResponse(BaseModel):
    """Lo que se ofrece hoy en los formularios: solo especies y razas activas."""

    species: list[SpeciesResponse]

    @classmethod
    def from_entities(cls, species: list[Species]) -> PetCatalogResponse:
        return cls(
            species=[
                SpeciesResponse(name=item.name, breeds=[breed.name for breed in item.breeds])
                for item in species
            ]
        )


class CatalogBreedResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    # "Sin especificar": no se renombra ni se desactiva.
    is_locked: bool

    @classmethod
    def from_entity(cls, breed: Breed) -> CatalogBreedResponse:
        return cls(
            id=breed.id or 0, name=breed.name, is_active=breed.is_active, is_locked=breed.is_locked
        )


class CatalogSpeciesResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    breeds: list[CatalogBreedResponse]

    @classmethod
    def from_entity(cls, species: Species) -> CatalogSpeciesResponse:
        return cls(
            id=species.id or 0,
            name=species.name,
            is_active=species.is_active,
            breeds=[CatalogBreedResponse.from_entity(breed) for breed in species.breeds],
        )


class ManagedCatalogResponse(BaseModel):
    """El catálogo completo para administrarlo, con lo desactivado incluido."""

    species: list[CatalogSpeciesResponse]


class CatalogNameRequest(BaseModel):
    # El largo exacto lo decide el dominio después de formatear el nombre.
    name: str = Field(min_length=1, max_length=MAX_BREED_LENGTH * 2)


class UpdateCatalogEntryRequest(CatalogNameRequest):
    is_active: bool

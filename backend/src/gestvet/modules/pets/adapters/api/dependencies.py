from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.pets.adapters.persistence.sqlalchemy_catalog_repository import (
    SqlAlchemyPetCatalogRepository,
)
from gestvet.modules.pets.adapters.persistence.sqlalchemy_pet_repository import (
    SqlAlchemyPetRepository,
)
from gestvet.modules.pets.ports.catalog_repository import PetCatalogRepository
from gestvet.modules.pets.ports.pet_repository import PetRepository


def get_pet_repository(session: SessionDep) -> PetRepository:
    return SqlAlchemyPetRepository(session)


PetRepositoryDep = Annotated[PetRepository, Depends(get_pet_repository)]


def get_pet_catalog_repository(session: SessionDep) -> PetCatalogRepository:
    return SqlAlchemyPetCatalogRepository(session)


PetCatalogRepositoryDep = Annotated[PetCatalogRepository, Depends(get_pet_catalog_repository)]

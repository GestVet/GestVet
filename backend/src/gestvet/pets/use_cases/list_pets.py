"""Caso de uso: listado paginado de mascotas."""

from __future__ import annotations

from gestvet.core.pagination import Page
from gestvet.pets.domain.entities import Pet
from gestvet.pets.ports.pet_repository import PetQuery, PetRepository


class ListPets:
    def __init__(self, pets: PetRepository) -> None:
        self._pets = pets

    async def __call__(self, query: PetQuery) -> Page[Pet]:
        return await self._pets.search(query)

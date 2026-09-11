"""Puerto de persistencia de mascotas.

Define qué necesita el negocio, nunca cómo se guarda.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page
from gestvet.modules.pets.domain.entities import Pet


@dataclass(frozen=True, slots=True)
class PetQuery:
    """Criterios de búsqueda.

    `owner_id` no es un filtro más: es la forma de aplicar la propiedad del
    recurso. Acotar el conjunto antes de buscar evita el error clásico de leer
    por identificador y recién después preguntar de quién era.
    """

    owner_id: int | None = None
    is_active: bool | None = None
    search: str | None = None
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


class PetRepository(Protocol):
    async def add(self, pet: Pet) -> Pet: ...

    async def get(self, pet_id: int, owner_id: int | None = None) -> Pet | None: ...

    async def search(self, query: PetQuery) -> Page[Pet]: ...

    async def save(self, pet: Pet) -> Pet: ...

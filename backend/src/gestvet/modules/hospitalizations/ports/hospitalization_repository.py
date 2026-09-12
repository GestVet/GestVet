"""Puerto de persistencia de internaciones."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page
from gestvet.modules.hospitalizations.domain.entities import Hospitalization


@dataclass(frozen=True, slots=True)
class HospitalizationQuery:
    pet_id: int
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


class HospitalizationRepository(Protocol):
    async def add(self, hospitalization: Hospitalization) -> Hospitalization: ...

    async def get(self, hospitalization_id: int) -> Hospitalization | None: ...

    async def save(self, hospitalization: Hospitalization) -> Hospitalization: ...

    async def search(self, query: HospitalizationQuery) -> Page[Hospitalization]: ...

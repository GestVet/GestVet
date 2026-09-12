"""Puerto de persistencia de la historia clínica.

Define qué necesita el negocio, nunca cómo se guarda.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gestvet.core.pagination import DEFAULT_PAGE_SIZE, Page
from gestvet.modules.medical_records.domain.entities import ClinicalEntry, EntryKind


@dataclass(frozen=True, slots=True)
class ClinicalEntryQuery:
    pet_id: int
    kind: EntryKind | None = None
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


class ClinicalEntryRepository(Protocol):
    async def add(self, entry: ClinicalEntry) -> ClinicalEntry: ...

    async def get(self, entry_id: int) -> ClinicalEntry | None: ...

    async def search(self, query: ClinicalEntryQuery) -> Page[ClinicalEntry]: ...

    async def list_all_for_pet(self, pet_id: int) -> list[ClinicalEntry]:
        """Historia completa, sin paginar, del más antiguo al más nuevo.

        Un reporte no puede recortar entradas: a diferencia de `search`, que
        sirve a una pantalla con paginación, esto lo usa el PDF, que necesita
        todo.
        """
        ...

"""Puerto de persistencia de especialidades veterinarias."""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.accounts.domain.specialties import Specialty


class SpecialtyRepository(Protocol):
    async def list_all(self, *, include_inactive: bool) -> list[Specialty]:
        """El catálogo, ordenado por categoría. Sin inactivas, solo lo que se ofrece."""
        ...

    async def get(self, specialty_id: int) -> Specialty | None: ...

    async def get_many(self, specialty_ids: frozenset[int]) -> list[Specialty]:
        """Solo las que existen. Quien llama compara el tamaño para saber qué falta."""
        ...

    async def find_id(self, key: str) -> int | None: ...

    async def add(self, specialty: Specialty) -> Specialty: ...

    async def save(self, specialty: Specialty) -> Specialty: ...

    async def specialties_for(self, user_ids: frozenset[int]) -> dict[int, list[Specialty]]:
        """Las especialidades de cada veterinario, para mostrarlas al elegir con quién reservar."""
        ...

    async def assign(self, user_id: int, specialty_ids: frozenset[int]) -> None:
        """Reemplaza el conjunto asignado al veterinario por este."""
        ...

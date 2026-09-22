"""Casos de uso: catálogo de especialidades y asignación a veterinarios.

Un veterinario necesita al menos una especialidad para que tenga sentido
ofrecerlo al filtrar por especialidad en la reserva: sin ninguna, no
aparecería nunca en ese filtro y la cuenta quedaría invisible para quien
busca justo lo que sabe atender.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity import Role
from gestvet.modules.accounts.domain.exceptions import (
    SpecialtiesRequired,
    SpecialtyNameTaken,
    SpecialtyNotFound,
    UnknownSpecialties,
    UserNotFound,
)
from gestvet.modules.accounts.domain.specialties import Specialty, SpecialtyCategory, specialty_key
from gestvet.modules.accounts.ports.specialty_repository import SpecialtyRepository
from gestvet.modules.accounts.ports.user_repository import UserRepository


async def _ensure_name_free(catalog: SpecialtyRepository, name: str, own_id: int | None) -> None:
    found = await catalog.find_id(specialty_key(name))
    if found is not None and found != own_id:
        raise SpecialtyNameTaken(name)


async def ensure_specialties_exist(
    catalog: SpecialtyRepository, specialty_ids: frozenset[int]
) -> None:
    """Todo identificador recibido tiene que corresponder a una especialidad real."""
    if not specialty_ids:
        raise SpecialtiesRequired()
    found = await catalog.get_many(specialty_ids)
    missing = specialty_ids - {specialty.id for specialty in found if specialty.id is not None}
    if missing:
        raise UnknownSpecialties(frozenset(missing))


@dataclass(frozen=True, slots=True)
class AddSpecialtyCommand:
    name: str
    category: SpecialtyCategory
    description: str = ""


class AddSpecialty:
    def __init__(self, catalog: SpecialtyRepository) -> None:
        self._catalog = catalog

    async def __call__(self, command: AddSpecialtyCommand) -> Specialty:
        candidate = Specialty(
            name=command.name, category=command.category, description=command.description
        )
        await _ensure_name_free(self._catalog, candidate.name, None)
        return await self._catalog.add(candidate)


@dataclass(frozen=True, slots=True)
class UpdateSpecialtyCommand:
    specialty_id: int
    name: str
    category: SpecialtyCategory
    description: str
    is_active: bool


class UpdateSpecialty:
    def __init__(self, catalog: SpecialtyRepository) -> None:
        self._catalog = catalog

    async def __call__(self, command: UpdateSpecialtyCommand) -> Specialty:
        specialty = await self._catalog.get(command.specialty_id)
        if specialty is None:
            raise SpecialtyNotFound(command.specialty_id)
        await _ensure_name_free(self._catalog, command.name.strip(), specialty.id)
        specialty.update(
            name=command.name,
            category=command.category,
            description=command.description,
            is_active=command.is_active,
        )
        return await self._catalog.save(specialty)


@dataclass(frozen=True, slots=True)
class AssignVeterinarianSpecialtiesCommand:
    actor_id: int
    veterinarian_id: int
    specialty_ids: frozenset[int]


class AssignVeterinarianSpecialties:
    """La administración decide con qué especialidades queda un veterinario."""

    def __init__(
        self,
        users: UserRepository,
        catalog: SpecialtyRepository,
        activity: ActivityRecorder,
    ) -> None:
        self._users = users
        self._catalog = catalog
        self._activity = activity

    async def __call__(self, command: AssignVeterinarianSpecialtiesCommand) -> list[Specialty]:
        user = await self._users.get(command.veterinarian_id)
        if user is None or user.role != Role.VETERINARIAN:
            raise UserNotFound(command.veterinarian_id)
        await ensure_specialties_exist(self._catalog, command.specialty_ids)

        await self._catalog.assign(command.veterinarian_id, command.specialty_ids)
        asignadas = await self._catalog.specialties_for(frozenset({command.veterinarian_id}))
        resultado = asignadas.get(command.veterinarian_id, [])
        await self._activity.record(
            command.actor_id,
            ActivityKind.STAFF_SPECIALTIES_UPDATED,
            f"{user.email}: {len(resultado)} especialidad(es)",
        )
        return resultado

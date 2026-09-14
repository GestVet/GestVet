"""Casos de uso del carnet de vacunas.

Registrar una vacuna es un acto clínico. Ver el carnet lo puede pedir el dueño,
solo de sus mascotas, o el personal, de cualquiera: la misma regla de la
historia clínica, aplicada acá para que ningún endpoint pueda olvidarla.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.medical_records.domain.exceptions import InvalidVaccination, PetNotFound
from gestvet.modules.medical_records.domain.vaccination import (
    VACCINES,
    Vaccination,
    VaccineCode,
    VaccineStatusSummary,
    suggested_interval_days,
    summarize,
    vaccines_for,
)
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory, PetSummary
from gestvet.modules.medical_records.ports.vaccination_repository import VaccinationRepository


async def _require_pet(pets: PetDirectory, pet_id: int) -> PetSummary:
    summary = await pets.summary(pet_id)
    if summary is None:
        raise PetNotFound(pet_id)
    return summary


async def require_pet_access(
    pets: PetDirectory, pet_id: int, *, requester_id: int, is_staff: bool
) -> None:
    # Una mascota ajena responde "no existe", igual que en la historia clínica.
    allowed = await (pets.exists(pet_id) if is_staff else pets.is_owned_by(pet_id, requester_id))
    if not allowed:
        raise PetNotFound(pet_id)


@dataclass(frozen=True, slots=True)
class RecordVaccinationCommand:
    pet_id: int
    veterinarian_id: int
    vaccine: VaccineCode
    applied_on: date
    next_due_on: date | None = None
    product_name: str = ""
    batch: str = ""
    notes: str = ""
    appointment_id: int | None = None


class RecordVaccination:
    def __init__(
        self,
        vaccinations: VaccinationRepository,
        pets: PetDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._vaccinations = vaccinations
        self._pets = pets
        self._activity = activity

    async def __call__(self, command: RecordVaccinationCommand) -> Vaccination:
        pet = await _require_pet(self._pets, command.pet_id)
        info = VACCINES[command.vaccine]
        if not info.applies_to(pet.species):
            raise InvalidVaccination(f"«{info.label}» no se aplica a la especie {pet.species}.")

        saved = await self._vaccinations.add(
            Vaccination(
                pet_id=command.pet_id,
                veterinarian_id=command.veterinarian_id,
                vaccine=command.vaccine,
                applied_on=command.applied_on,
                next_due_on=command.next_due_on,
                product_name=command.product_name,
                batch=command.batch,
                notes=command.notes,
                appointment_id=command.appointment_id,
            )
        )
        await self._activity.record(
            command.veterinarian_id,
            ActivityKind.CLINICAL_ENTRY_ADDED,
            f"Vacuna {saved.label} (mascota {saved.pet_id})",
        )
        return saved


@dataclass(frozen=True, slots=True)
class VaccinationCard:
    summary: list[VaccineStatusSummary]
    items: list[Vaccination]


class GetVaccinationCard:
    def __init__(self, vaccinations: VaccinationRepository, pets: PetDirectory) -> None:
        self._vaccinations = vaccinations
        self._pets = pets

    async def __call__(
        self, pet_id: int, *, requester_id: int, is_staff: bool, today: date
    ) -> VaccinationCard:
        await require_pet_access(self._pets, pet_id, requester_id=requester_id, is_staff=is_staff)
        items = await self._vaccinations.list_for_pet(pet_id)
        return VaccinationCard(summary=summarize(items, today), items=items)


@dataclass(frozen=True, slots=True)
class VaccineOption:
    vaccine: VaccineCode
    label: str
    # Días hasta la próxima dosis si se aplica hoy; `None` si no lleva refuerzo.
    interval_days: int | None


class ListVaccineOptions:
    """Qué vacunas se le pueden registrar a una mascota y cada cuánto se refuerzan."""

    def __init__(self, pets: PetDirectory) -> None:
        self._pets = pets

    async def __call__(self, pet_id: int, today: date) -> list[VaccineOption]:
        pet = await _require_pet(self._pets, pet_id)
        return [
            VaccineOption(
                vaccine=code,
                label=info.label,
                interval_days=suggested_interval_days(
                    code, applied_on=today, birth_date=pet.birth_date
                ),
            )
            for code, info in vaccines_for(pet.species)
        ]

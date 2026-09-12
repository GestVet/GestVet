"""Caso de uso: agregar una entrada a la historia clínica de una mascota."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.medical_records.domain.entities import ClinicalEntry, EntryKind
from gestvet.modules.medical_records.domain.exceptions import PetNotFound
from gestvet.modules.medical_records.ports.clinical_entry_repository import ClinicalEntryRepository
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory


@dataclass(frozen=True, slots=True)
class AddClinicalEntryCommand:
    pet_id: int
    veterinarian_id: int
    kind: EntryKind
    notes: str
    diagnosis: str = ""
    treatment: str = ""
    weight_kg: Decimal | None = None
    appointment_id: int | None = None
    occurred_at: datetime | None = None


class AddClinicalEntry:
    def __init__(
        self,
        entries: ClinicalEntryRepository,
        pets: PetDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._entries = entries
        self._pets = pets
        self._activity = activity

    async def __call__(self, command: AddClinicalEntryCommand) -> ClinicalEntry:
        if not await self._pets.exists(command.pet_id):
            raise PetNotFound(command.pet_id)

        entry = ClinicalEntry(
            pet_id=command.pet_id,
            veterinarian_id=command.veterinarian_id,
            kind=command.kind,
            notes=command.notes,
            diagnosis=command.diagnosis,
            treatment=command.treatment,
            weight_kg=command.weight_kg,
            appointment_id=command.appointment_id,
            occurred_at=command.occurred_at or datetime.now(UTC),
        )

        guardada = await self._entries.add(entry)
        await self._activity.record(
            command.veterinarian_id,
            ActivityKind.CLINICAL_ENTRY_ADDED,
            f"{guardada.kind.label} (mascota {guardada.pet_id})",
        )
        return guardada

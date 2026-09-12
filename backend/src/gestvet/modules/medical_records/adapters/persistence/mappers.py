"""Traducción entre la fila de la tabla y la entidad de dominio.

Este archivo es la razón por la que el dominio puede ignorar SQLAlchemy.
"""

from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.medical_records.adapters.persistence.models import ClinicalEntryRow
from gestvet.modules.medical_records.domain.entities import ClinicalEntry, EntryKind


def row_to_entity(row: ClinicalEntryRow) -> ClinicalEntry:
    return ClinicalEntry(
        id=row.id,
        pet_id=row.pet_id,
        veterinarian_id=row.veterinarian_id,
        appointment_id=row.appointment_id,
        kind=EntryKind(row.kind),
        notes=row.notes,
        diagnosis=row.diagnosis,
        treatment=row.treatment,
        weight_kg=row.weight_kg,
        occurred_at=as_utc(row.occurred_at),
        created_at=as_utc(row.created_at),
    )


def entity_to_row(entry: ClinicalEntry) -> ClinicalEntryRow:
    return ClinicalEntryRow(
        pet_id=entry.pet_id,
        veterinarian_id=entry.veterinarian_id,
        appointment_id=entry.appointment_id,
        kind=entry.kind.value,
        notes=entry.notes,
        diagnosis=entry.diagnosis,
        treatment=entry.treatment,
        weight_kg=entry.weight_kg,
        occurred_at=entry.occurred_at,
        created_at=entry.created_at,
    )

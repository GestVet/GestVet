"""Traducción entre la fila de la tabla y la entidad de dominio."""

from __future__ import annotations

from gestvet.core.timestamps import as_utc
from gestvet.modules.hospitalizations.adapters.persistence.models import (
    HospitalizationNoteRow,
    HospitalizationRow,
)
from gestvet.modules.hospitalizations.domain.entities import (
    Hospitalization,
    HospitalizationNote,
    HospitalizationStatus,
)


def row_to_entity(row: HospitalizationRow) -> Hospitalization:
    return Hospitalization(
        id=row.id,
        appointment_id=row.appointment_id,
        pet_id=row.pet_id,
        opened_by=row.opened_by,
        reason=row.reason,
        status=HospitalizationStatus(row.status),
        discharge_notes=row.discharge_notes,
        admitted_at=as_utc(row.admitted_at),
        discharged_at=as_utc(row.discharged_at) if row.discharged_at is not None else None,
    )


def entity_to_row(hospitalization: Hospitalization) -> HospitalizationRow:
    return HospitalizationRow(
        appointment_id=hospitalization.appointment_id,
        pet_id=hospitalization.pet_id,
        opened_by=hospitalization.opened_by,
        reason=hospitalization.reason,
        status=hospitalization.status.value,
        discharge_notes=hospitalization.discharge_notes,
        admitted_at=hospitalization.admitted_at,
        discharged_at=hospitalization.discharged_at,
    )


def note_row_to_entity(row: HospitalizationNoteRow) -> HospitalizationNote:
    return HospitalizationNote(
        id=row.id,
        hospitalization_id=row.hospitalization_id,
        author_id=row.author_id,
        note=row.note,
        created_at=as_utc(row.created_at),
    )


def note_entity_to_row(note: HospitalizationNote) -> HospitalizationNoteRow:
    return HospitalizationNoteRow(
        hospitalization_id=note.hospitalization_id,
        author_id=note.author_id,
        note=note.note,
        created_at=note.created_at,
    )

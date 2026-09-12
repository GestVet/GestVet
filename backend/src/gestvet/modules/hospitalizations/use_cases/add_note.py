"""Caso de uso: agregar una nota de seguimiento a una internación abierta."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.hospitalizations.domain.entities import HospitalizationNote
from gestvet.modules.hospitalizations.domain.exceptions import (
    HospitalizationAlreadyDischarged,
    HospitalizationNotFound,
)
from gestvet.modules.hospitalizations.ports.hospitalization_repository import (
    HospitalizationRepository,
)
from gestvet.modules.hospitalizations.ports.note_repository import NoteRepository


@dataclass(frozen=True, slots=True)
class AddNoteCommand:
    hospitalization_id: int
    author_id: int
    note: str


class AddNote:
    def __init__(
        self,
        notes: NoteRepository,
        hospitalizations: HospitalizationRepository,
        activity: ActivityRecorder,
    ) -> None:
        self._notes = notes
        self._hospitalizations = hospitalizations
        self._activity = activity

    async def __call__(self, command: AddNoteCommand) -> HospitalizationNote:
        hospitalization = await self._hospitalizations.get(command.hospitalization_id)
        if hospitalization is None:
            raise HospitalizationNotFound(command.hospitalization_id)
        if not hospitalization.is_open:
            raise HospitalizationAlreadyDischarged(command.hospitalization_id)

        note = HospitalizationNote(
            hospitalization_id=command.hospitalization_id,
            author_id=command.author_id,
            note=command.note,
        )
        guardada = await self._notes.add(note)
        await self._activity.record(
            command.author_id, ActivityKind.HOSPITALIZATION_NOTE_ADDED, guardada.note
        )
        return guardada

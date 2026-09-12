"""Puerto de persistencia de las notas de seguimiento."""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.hospitalizations.domain.entities import HospitalizationNote


class NoteRepository(Protocol):
    async def add(self, note: HospitalizationNote) -> HospitalizationNote: ...

    async def list_for_hospitalization(
        self, hospitalization_id: int
    ) -> list[HospitalizationNote]: ...

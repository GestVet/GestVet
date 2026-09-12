"""Caso de uso: armar el PDF con toda la historia clínica de una mascota.

Misma regla de autorización que `ListClinicalEntries`: el personal pide la de
cualquier mascota, un cliente solo la de las suyas. Se repite acá en vez de
reutilizar esa clase porque el resultado es distinto (bytes de un PDF, no una
página de entradas) y las dos reglas son una comprobación de una línea cada
una: la duplicación es más barata que la abstracción.
"""

from __future__ import annotations

import asyncio

from gestvet.modules.medical_records.domain.exceptions import PetNotFound
from gestvet.modules.medical_records.ports.attachment_repository import AttachmentRepository
from gestvet.modules.medical_records.ports.clinical_entry_repository import (
    ClinicalEntryRepository,
)
from gestvet.modules.medical_records.ports.clinical_history_report import (
    ClinicalHistoryReportRenderer,
)
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory, PetSummary


class BuildClinicalHistoryReport:
    def __init__(
        self,
        entries: ClinicalEntryRepository,
        attachments: AttachmentRepository,
        pets: PetDirectory,
        renderer: ClinicalHistoryReportRenderer,
    ) -> None:
        self._entries = entries
        self._attachments = attachments
        self._pets = pets
        self._renderer = renderer

    async def __call__(
        self, pet_id: int, *, requester_id: int, is_staff: bool
    ) -> tuple[str, bytes]:
        summary = await self._authorize(pet_id, requester_id=requester_id, is_staff=is_staff)

        history = await self._entries.list_all_for_pet(pet_id)
        attachments_by_entry = {
            entry.id or 0: await self._attachments.list_for_entry(entry.id or 0)
            for entry in history
        }

        pdf_bytes = await asyncio.to_thread(
            self._renderer.render, summary, history, attachments_by_entry
        )
        return summary.name, pdf_bytes

    async def _authorize(self, pet_id: int, *, requester_id: int, is_staff: bool) -> PetSummary:
        if is_staff:
            summary = await self._pets.summary(pet_id)
            if summary is None:
                raise PetNotFound(pet_id)
            return summary

        # Misma respuesta para "no existe" y "es de otro dueño": distinguirlas
        # confirmaría que el identificador pertenece a alguien.
        if not await self._pets.is_owned_by(pet_id, requester_id):
            raise PetNotFound(pet_id)
        summary = await self._pets.summary(pet_id)
        if summary is None:
            raise PetNotFound(pet_id)
        return summary

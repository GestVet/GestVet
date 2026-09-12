"""Caso de uso: consultar la historia clínica de una mascota.

Un cliente solo ve la de sus propias mascotas; el personal ve la de
cualquiera, porque la necesita para atender. La comprobación de propiedad
vive acá y no en el adaptador HTTP, para que ningún endpoint nuevo pueda
olvidarla.
"""

from __future__ import annotations

from gestvet.core.pagination import Page
from gestvet.modules.medical_records.domain.entities import ClinicalEntry
from gestvet.modules.medical_records.domain.exceptions import PetNotFound
from gestvet.modules.medical_records.ports.clinical_entry_repository import (
    ClinicalEntryQuery,
    ClinicalEntryRepository,
)
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory


class ListClinicalEntries:
    def __init__(self, entries: ClinicalEntryRepository, pets: PetDirectory) -> None:
        self._entries = entries
        self._pets = pets

    async def __call__(
        self, query: ClinicalEntryQuery, *, requester_id: int, is_staff: bool
    ) -> Page[ClinicalEntry]:
        if is_staff:
            if not await self._pets.exists(query.pet_id):
                raise PetNotFound(query.pet_id)
        # Una mascota ajena responde "no existe" y no "no podés": responder
        # distinto confirmaría que ese identificador pertenece a alguien.
        elif not await self._pets.is_owned_by(query.pet_id, requester_id):
            raise PetNotFound(query.pet_id)

        return await self._entries.search(query)

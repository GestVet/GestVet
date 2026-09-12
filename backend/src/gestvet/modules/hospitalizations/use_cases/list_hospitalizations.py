"""Caso de uso: consultar las internaciones de una mascota.

Un cliente solo ve las de sus propias mascotas; el personal, las de
cualquiera, porque las necesita para atender.
"""

from __future__ import annotations

from gestvet.core.pagination import Page
from gestvet.modules.hospitalizations.domain.entities import Hospitalization
from gestvet.modules.hospitalizations.domain.exceptions import PetNotFound
from gestvet.modules.hospitalizations.ports.hospitalization_repository import (
    HospitalizationQuery,
    HospitalizationRepository,
)
from gestvet.modules.hospitalizations.ports.pet_directory import PetDirectory


class ListHospitalizations:
    def __init__(self, hospitalizations: HospitalizationRepository, pets: PetDirectory) -> None:
        self._hospitalizations = hospitalizations
        self._pets = pets

    async def __call__(
        self, query: HospitalizationQuery, *, requester_id: int, is_staff: bool
    ) -> Page[Hospitalization]:
        if is_staff:
            if not await self._pets.exists(query.pet_id):
                raise PetNotFound(query.pet_id)
        # Una mascota ajena responde "no existe" y no "no podés": responder
        # distinto confirmaría que ese identificador pertenece a alguien.
        elif not await self._pets.is_owned_by(query.pet_id, requester_id):
            raise PetNotFound(query.pet_id)

        return await self._hospitalizations.search(query)

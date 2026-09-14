"""Casos de uso del carnet de vacunas compartible.

El PDF lo baja el dueño o el personal, con la misma regla de acceso que el
carnet en pantalla. Lleva un código QR con un enlace firmado: quien lo escanea
(otra veterinaria, la municipalidad) ve el estado actual de las vacunas sin
iniciar sesión, y sin ningún dato de la persona dueña.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from gestvet.core.clinic_time import clinic_date
from gestvet.core.signed_links import SignedLinks
from gestvet.modules.medical_records.domain.exceptions import InvalidCardLink, PetNotFound
from gestvet.modules.medical_records.domain.vaccination import VaccineStatusSummary, summarize
from gestvet.modules.medical_records.ports.pet_directory import PetDirectory
from gestvet.modules.medical_records.ports.vaccination_card_report import (
    VaccinationCardDocument,
    VaccinationCardRenderer,
)
from gestvet.modules.medical_records.ports.vaccination_repository import VaccinationRepository
from gestvet.modules.medical_records.use_cases.vaccinations import require_pet_access

# Un año: alcanza para un trámite o una mudanza de clínica. Después se baja un
# carnet nuevo, que trae un enlace nuevo.
CARD_LINK_DAYS = 365
CARD_LINK_PURPOSE = "vaccination-card"


@dataclass(frozen=True, slots=True)
class CardRequest:
    pet_id: int
    requester_id: int
    is_staff: bool
    now: datetime
    # Dónde vive la página pública que abre el QR.
    verification_base_url: str


class BuildVaccinationCardPdf:
    def __init__(
        self,
        vaccinations: VaccinationRepository,
        pets: PetDirectory,
        renderer: VaccinationCardRenderer,
        links: SignedLinks,
    ) -> None:
        self._vaccinations = vaccinations
        self._pets = pets
        self._renderer = renderer
        self._links = links

    async def __call__(self, request: CardRequest) -> tuple[str, bytes]:
        await require_pet_access(
            self._pets, request.pet_id, requester_id=request.requester_id, is_staff=request.is_staff
        )
        pet = await self._pets.summary(request.pet_id)
        if pet is None:
            raise PetNotFound(request.pet_id)

        items = await self._vaccinations.list_for_pet(request.pet_id)
        today = clinic_date(request.now)
        expires_at = request.now + timedelta(days=CARD_LINK_DAYS)
        token = self._links.sign(request.pet_id, expires_at)
        document = VaccinationCardDocument(
            pet=pet,
            summary=summarize(items, today),
            items=items,
            verification_url=f"{request.verification_base_url.rstrip('/')}/carnet/{token}",
            issued_on=today,
            valid_until=clinic_date(expires_at),
        )
        pdf = await asyncio.to_thread(self._renderer.render, document)
        return pet.name, pdf


@dataclass(frozen=True, slots=True)
class PublicVaccinationCard:
    """Lo que ve quien escanea el QR: la mascota y sus vacunas, nada de la persona."""

    pet_name: str
    species: str
    breed: str
    microchip_number: str
    summary: list[VaccineStatusSummary]
    checked_on: date
    valid_until: date


class VerifyVaccinationCard:
    def __init__(
        self, vaccinations: VaccinationRepository, pets: PetDirectory, links: SignedLinks
    ) -> None:
        self._vaccinations = vaccinations
        self._pets = pets
        self._links = links

    async def __call__(self, token: str, now: datetime) -> PublicVaccinationCard:
        reference = self._links.read(token, now)
        pet = None if reference is None else await self._pets.summary(reference.subject_id)
        if reference is None or pet is None:
            raise InvalidCardLink()
        today = clinic_date(now)
        items = await self._vaccinations.list_for_pet(reference.subject_id)
        return PublicVaccinationCard(
            pet_name=pet.name,
            species=pet.species,
            breed=pet.breed,
            microchip_number=pet.microchip_number,
            summary=summarize(items, today),
            checked_on=today,
            valid_until=clinic_date(reference.expires_at),
        )

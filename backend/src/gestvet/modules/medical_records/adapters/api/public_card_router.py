"""Verificación pública del carnet de vacunas.

Es la única ruta del módulo sin sesión: la abre quien escanea el QR del carnet.
No devuelve nada de la persona dueña, y un enlace alterado o vencido responde
lo mismo que uno inexistente.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status
from pydantic import BaseModel

from gestvet.modules.medical_records.adapters.api.dependencies import (
    CardLinksDep,
    PetDirectoryDep,
    VaccinationRepositoryDep,
)
from gestvet.modules.medical_records.adapters.api.vaccination_schemas import (
    VaccineStatusResponse,
)
from gestvet.modules.medical_records.domain.exceptions import InvalidCardLink
from gestvet.modules.medical_records.use_cases.vaccination_card_document import (
    VerifyVaccinationCard,
)

router = APIRouter()

# Un enlace firmado no llega a esto; un texto más largo no es un carnet.
MAX_TOKEN_LENGTH = 300


class PublicVaccinationCardResponse(BaseModel):
    pet_name: str
    species: str
    breed: str
    microchip_number: str
    summary: list[VaccineStatusResponse]
    checked_on: date
    valid_until: date


@router.get(
    "/{token}",
    response_model=PublicVaccinationCardResponse,
    summary="Verificar un carnet de vacunas desde su código QR",
)
async def verify_vaccination_card(
    token: Annotated[str, Path(max_length=MAX_TOKEN_LENGTH)],
    vaccinations: VaccinationRepositoryDep,
    pets: PetDirectoryDep,
    links: CardLinksDep,
) -> PublicVaccinationCardResponse:
    try:
        card = await VerifyVaccinationCard(vaccinations, pets, links)(token, datetime.now(UTC))
    except InvalidCardLink as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return PublicVaccinationCardResponse(
        pet_name=card.pet_name,
        species=card.species,
        breed=card.breed,
        microchip_number=card.microchip_number,
        summary=[VaccineStatusResponse.from_summary(item) for item in card.summary],
        checked_on=card.checked_on,
        valid_until=card.valid_until,
    )

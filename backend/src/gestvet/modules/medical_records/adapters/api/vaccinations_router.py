"""Adaptador de entrada HTTP del carnet de vacunas.

Registrar exige escribir en la historia clínica; ver el carnet, leerla. El
recorte a las mascotas propias de un cliente lo aplica el caso de uso.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.clinic_time import clinic_date
from gestvet.core.config import get_settings
from gestvet.core.identity import STAFF_ROLES, Principal
from gestvet.core.permissions import Permission
from gestvet.modules.medical_records.adapters.api.dependencies import (
    CardLinksDep,
    PetDirectoryDep,
    VaccinationCardRendererDep,
    VaccinationRepositoryDep,
)
from gestvet.modules.medical_records.adapters.api.vaccination_schemas import (
    RecordVaccinationRequest,
    VaccinationCardResponse,
    VaccinationResponse,
    VaccineOptionListResponse,
    VaccineOptionResponse,
)
from gestvet.modules.medical_records.domain.exceptions import InvalidVaccination, PetNotFound
from gestvet.modules.medical_records.use_cases.vaccination_card_document import (
    BuildVaccinationCardPdf,
    CardRequest,
)
from gestvet.modules.medical_records.use_cases.vaccinations import (
    GetVaccinationCard,
    ListVaccineOptions,
    RecordVaccination,
    RecordVaccinationCommand,
)

router = APIRouter()

ClinicalWriterDep = Annotated[
    Principal, Depends(require_permission(Permission.CLINICAL_RECORDS_WRITE))
]
ClinicalReaderDep = Annotated[
    Principal, Depends(require_permission(Permission.CLINICAL_RECORDS_READ))
]
PetIdQuery = Annotated[int, Query(ge=1, description="Mascota consultada")]


def _today() -> datetime:
    return datetime.now(UTC)


@router.get("", response_model=VaccinationCardResponse, summary="Carnet de vacunas de una mascota")
async def read_vaccination_card(
    principal: ClinicalReaderDep,
    vaccinations: VaccinationRepositoryDep,
    pets: PetDirectoryDep,
    pet_id: PetIdQuery,
) -> VaccinationCardResponse:
    try:
        card = await GetVaccinationCard(vaccinations, pets)(
            pet_id,
            requester_id=principal.user_id,
            is_staff=principal.role in STAFF_ROLES,
            today=clinic_date(_today()),
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return VaccinationCardResponse.from_card(card)


@router.get(
    "/options",
    response_model=VaccineOptionListResponse,
    summary="Vacunas que se le pueden registrar a una mascota",
)
async def list_vaccine_options(
    veterinarian: ClinicalWriterDep,
    pets: PetDirectoryDep,
    pet_id: PetIdQuery,
) -> VaccineOptionListResponse:
    try:
        options = await ListVaccineOptions(pets)(pet_id, clinic_date(_today()))
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return VaccineOptionListResponse(
        items=[VaccineOptionResponse.from_option(option) for option in options]
    )


@router.post(
    "",
    response_model=VaccinationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una vacuna",
)
async def record_vaccination(
    payload: RecordVaccinationRequest,
    veterinarian: ClinicalWriterDep,
    vaccinations: VaccinationRepositoryDep,
    pets: PetDirectoryDep,
    activity: ActivityRecorderDep,
) -> VaccinationResponse:
    try:
        vaccination = await RecordVaccination(vaccinations, pets, activity)(
            RecordVaccinationCommand(
                pet_id=payload.pet_id,
                veterinarian_id=veterinarian.user_id,
                vaccine=payload.vaccine,
                applied_on=payload.applied_on,
                next_due_on=payload.next_due_on,
                product_name=payload.product_name,
                batch=payload.batch,
                notes=payload.notes,
                appointment_id=payload.appointment_id,
            )
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidVaccination as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return VaccinationResponse.from_entity(vaccination)


def _card_filename(pet_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", pet_name.lower()).strip("-") or "mascota"
    return f"carnet-de-vacunas-{slug}.pdf"


@router.get("/card.pdf", summary="Descargar el carnet de vacunas en PDF, con QR de verificación")
async def download_vaccination_card(
    principal: ClinicalReaderDep,
    vaccinations: VaccinationRepositoryDep,
    pets: PetDirectoryDep,
    renderer: VaccinationCardRendererDep,
    links: CardLinksDep,
    pet_id: PetIdQuery,
) -> Response:
    try:
        pet_name, pdf = await BuildVaccinationCardPdf(vaccinations, pets, renderer, links)(
            CardRequest(
                pet_id=pet_id,
                requester_id=principal.user_id,
                is_staff=principal.role in STAFF_ROLES,
                now=_today(),
                verification_base_url=get_settings().frontend_base_url,
            )
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_card_filename(pet_name)}"'},
    )

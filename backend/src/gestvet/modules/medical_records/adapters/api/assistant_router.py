"""Adaptador de entrada HTTP del asistente de IA de la historia clínica.

Solo quien escribe la historia clínica (el veterinario) pide un resumen: cada
pedido cuesta dinero y el resumen sirve para atender, no para el dueño. Es un
POST porque genera algo nuevo cada vez y no debe quedar en ninguna caché.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from gestvet.core.auth import require_permission
from gestvet.core.clinic_time import clinic_date
from gestvet.core.identity import Principal
from gestvet.core.llm import LlmUnavailable
from gestvet.core.permissions import Permission
from gestvet.modules.medical_records.adapters.api.dependencies import (
    ClinicalEntryRepositoryDep,
    LlmClientDep,
    PetDirectoryDep,
    VaccinationRepositoryDep,
)
from gestvet.modules.medical_records.domain.clinical_summary import ClinicalSummary
from gestvet.modules.medical_records.domain.exceptions import PetNotFound
from gestvet.modules.medical_records.use_cases.summarize_clinical_history import (
    SummarizeClinicalHistory,
)

router = APIRouter()

ClinicalWriterDep = Annotated[
    Principal, Depends(require_permission(Permission.CLINICAL_RECORDS_WRITE))
]


class ClinicalSummaryRequest(BaseModel):
    pet_id: int = Field(ge=1)


class ClinicalSummaryResponse(BaseModel):
    summary: str
    alerts: list[str]
    follow_ups: list[str]
    model: str
    generated_at: datetime

    @classmethod
    def from_summary(cls, result: ClinicalSummary) -> ClinicalSummaryResponse:
        return cls(
            summary=result.summary,
            alerts=list(result.alerts),
            follow_ups=list(result.follow_ups),
            model=result.model,
            generated_at=datetime.now(UTC),
        )


@router.post(
    "/summary",
    response_model=ClinicalSummaryResponse,
    summary="Resumir con IA la historia clínica de una mascota",
)
async def summarize_clinical_history(
    payload: ClinicalSummaryRequest,
    veterinarian: ClinicalWriterDep,
    entries: ClinicalEntryRepositoryDep,
    vaccinations: VaccinationRepositoryDep,
    pets: PetDirectoryDep,
    llm: LlmClientDep,
) -> ClinicalSummaryResponse:
    try:
        result = await SummarizeClinicalHistory(entries, vaccinations, pets, llm)(
            payload.pet_id, clinic_date(datetime.now(UTC))
        )
    except PetNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except LlmUnavailable as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    return ClinicalSummaryResponse.from_summary(result)

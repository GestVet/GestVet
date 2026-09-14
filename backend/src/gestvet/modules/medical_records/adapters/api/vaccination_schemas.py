"""Contrato HTTP del carnet de vacunas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from gestvet.modules.medical_records.domain.vaccination import (
    MAX_BATCH_LENGTH,
    MAX_PRODUCT_LENGTH,
    MAX_VACCINATION_NOTES_LENGTH,
    Vaccination,
    VaccinationStatus,
    VaccineCode,
    VaccineStatusSummary,
)
from gestvet.modules.medical_records.use_cases.vaccinations import VaccinationCard, VaccineOption


class RecordVaccinationRequest(BaseModel):
    pet_id: int = Field(ge=1)
    vaccine: VaccineCode
    applied_on: date
    # Sin fecha, la vacuna no lleva refuerzo.
    next_due_on: date | None = None
    product_name: str = Field(default="", max_length=MAX_PRODUCT_LENGTH)
    batch: str = Field(default="", max_length=MAX_BATCH_LENGTH)
    notes: str = Field(default="", max_length=MAX_VACCINATION_NOTES_LENGTH)
    appointment_id: int | None = Field(default=None, ge=1)


class VaccinationResponse(BaseModel):
    id: int
    pet_id: int
    veterinarian_id: int
    vaccine: VaccineCode
    vaccine_label: str
    applied_on: date
    next_due_on: date | None
    product_name: str
    batch: str
    notes: str
    created_at: datetime

    @classmethod
    def from_entity(cls, vaccination: Vaccination) -> VaccinationResponse:
        return cls(
            id=vaccination.id or 0,
            pet_id=vaccination.pet_id,
            veterinarian_id=vaccination.veterinarian_id,
            vaccine=vaccination.vaccine,
            vaccine_label=vaccination.label,
            applied_on=vaccination.applied_on,
            next_due_on=vaccination.next_due_on,
            product_name=vaccination.product_name,
            batch=vaccination.batch,
            notes=vaccination.notes,
            created_at=vaccination.created_at,
        )


class VaccineStatusResponse(BaseModel):
    vaccine: VaccineCode
    label: str
    last_applied_on: date
    next_due_on: date | None
    status: VaccinationStatus
    status_label: str

    @classmethod
    def from_summary(cls, summary: VaccineStatusSummary) -> VaccineStatusResponse:
        return cls(
            vaccine=summary.vaccine,
            label=summary.label,
            last_applied_on=summary.last_applied_on,
            next_due_on=summary.next_due_on,
            status=summary.status,
            status_label=summary.status.label,
        )


class VaccinationCardResponse(BaseModel):
    """El estado de cada vacuna, lo más urgente primero, y todas las aplicaciones."""

    summary: list[VaccineStatusResponse]
    items: list[VaccinationResponse]

    @classmethod
    def from_card(cls, card: VaccinationCard) -> VaccinationCardResponse:
        return cls(
            summary=[VaccineStatusResponse.from_summary(item) for item in card.summary],
            items=[VaccinationResponse.from_entity(item) for item in card.items],
        )


class VaccineOptionResponse(BaseModel):
    vaccine: VaccineCode
    label: str
    interval_days: int | None

    @classmethod
    def from_option(cls, option: VaccineOption) -> VaccineOptionResponse:
        return cls(vaccine=option.vaccine, label=option.label, interval_days=option.interval_days)


class VaccineOptionListResponse(BaseModel):
    items: list[VaccineOptionResponse]

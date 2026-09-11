"""Contrato HTTP del módulo de citas.

Ningún cuerpo acepta `client_id`: el servidor lo toma de la credencial.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import AwareDatetime, BaseModel, Field

from gestvet.appointments.domain.entities import (
    MAX_DESCRIPTION_LENGTH,
    MAX_REASON_LENGTH,
    Appointment,
    AppointmentStatus,
    AppointmentType,
)


class BookAppointmentRequest(BaseModel):
    pet_id: int = Field(ge=1)
    veterinarian_id: int = Field(ge=1)
    appointment_type_id: int = Field(ge=1)
    scheduled_at: AwareDatetime
    description: str = Field(default="", max_length=MAX_DESCRIPTION_LENGTH)


class OpenEmergencyRequest(BaseModel):
    pet_id: int = Field(ge=1)
    description: str = Field(default="", max_length=MAX_DESCRIPTION_LENGTH)


class CancelAppointmentRequest(BaseModel):
    # Obligatoria: quien cancela le debe una explicación a la otra parte.
    reason: str = Field(min_length=1, max_length=MAX_REASON_LENGTH)


class AppointmentTypeResponse(BaseModel):
    id: int
    name: str
    duration_minutes: int
    price: Decimal
    is_emergency: bool

    @classmethod
    def from_entity(cls, appointment_type: AppointmentType) -> AppointmentTypeResponse:
        return cls(
            id=appointment_type.id or 0,
            name=appointment_type.name,
            duration_minutes=int(appointment_type.duration.total_seconds() // 60),
            price=appointment_type.price,
            is_emergency=appointment_type.is_emergency,
        )


class AppointmentTypeListResponse(BaseModel):
    items: list[AppointmentTypeResponse]
    total: int


class AppointmentResponse(BaseModel):
    id: int
    scheduled_at: datetime
    ends_at: datetime
    duration_minutes: int
    client_id: int
    pet_id: int
    veterinarian_id: int
    appointment_type_id: int
    description: str
    status: AppointmentStatus
    status_label: str
    cancellation_reason: str
    updated_by: int | None
    created_at: datetime

    @classmethod
    def from_entity(cls, appointment: Appointment) -> AppointmentResponse:
        return cls(
            id=appointment.id or 0,
            scheduled_at=appointment.scheduled_at,
            ends_at=appointment.ends_at,
            duration_minutes=int(appointment.duration.total_seconds() // 60),
            client_id=appointment.client_id,
            pet_id=appointment.pet_id,
            veterinarian_id=appointment.veterinarian_id,
            appointment_type_id=appointment.appointment_type_id,
            description=appointment.description,
            status=appointment.status,
            status_label=appointment.status.label,
            cancellation_reason=appointment.cancellation_reason,
            updated_by=appointment.updated_by,
            created_at=appointment.created_at,
        )


class AppointmentPageResponse(BaseModel):
    items: list[AppointmentResponse]
    total: int

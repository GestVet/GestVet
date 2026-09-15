"""Contrato HTTP del módulo de citas.

Ningún cuerpo acepta `client_id`: el servidor lo toma de la credencial.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import AwareDatetime, BaseModel, Field

from gestvet.modules.appointments.domain.entities import (
    MAX_DESCRIPTION_LENGTH,
    MAX_REASON_LENGTH,
    Appointment,
    AppointmentStatus,
    AppointmentType,
)
from gestvet.modules.appointments.use_cases.list_open_times import DayOpenTimes, SlotStatus


class BookAppointmentRequest(BaseModel):
    pet_id: int = Field(ge=1)
    veterinarian_id: int = Field(ge=1)
    appointment_type_id: int = Field(ge=1)
    scheduled_at: AwareDatetime
    description: str = Field(default="", max_length=MAX_DESCRIPTION_LENGTH)


class OpenEmergencyRequest(BaseModel):
    pet_id: int = Field(ge=1)
    description: str = Field(default="", max_length=MAX_DESCRIPTION_LENGTH)


class OpenWalkInEmergencyRequest(BaseModel):
    """La única excepción a la regla del módulo: acá sí viaja `client_id`.

    Lo abre el personal por un cliente que recién se dio de alta en el
    mostrador, así que no hay una sesión de cliente de la que tomarlo.
    """

    client_id: int = Field(ge=1)
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
        status = appointment.effective_status()
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
            status=status,
            status_label=status.label,
            cancellation_reason=appointment.cancellation_reason,
            updated_by=appointment.updated_by,
            created_at=appointment.created_at,
        )


class AppointmentPageResponse(BaseModel):
    items: list[AppointmentResponse]
    total: int


class ScheduleWindowResponse(BaseModel):
    starts_at: datetime
    ends_at: datetime


class GridSlotResponse(BaseModel):
    time: datetime
    status: SlotStatus


class VeterinarianOpenTimesResponse(BaseModel):
    veterinarian_id: int
    windows: list[ScheduleWindowResponse]
    slots: list[GridSlotResponse]


class DayOpenTimesResponse(BaseModel):
    """Un día con turnos publicados. `day` es la fecha en el calendario de la clínica."""

    day: date
    veterinarians: list[VeterinarianOpenTimesResponse]


class OpenTimesResponse(BaseModel):
    """Trae los días con al menos un turno, con cada cuarto de hora y su estado."""

    days: list[DayOpenTimesResponse]

    @classmethod
    def from_days(cls, days: list[DayOpenTimes]) -> OpenTimesResponse:
        return cls(
            days=[
                DayOpenTimesResponse(
                    day=item.day,
                    veterinarians=[
                        VeterinarianOpenTimesResponse(
                            veterinarian_id=vet.veterinarian_id,
                            windows=[
                                ScheduleWindowResponse(starts_at=w.starts_at, ends_at=w.ends_at)
                                for w in vet.windows
                            ],
                            slots=[
                                GridSlotResponse(time=s.time, status=s.status) for s in vet.slots
                            ],
                        )
                        for vet in item.veterinarians
                    ],
                )
                for item in days
            ]
        )

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from gestvet.core.timestamps import as_utc
from gestvet.modules.appointments.adapters.persistence.models import (
    AppointmentRow,
    AppointmentTypeRow,
)
from gestvet.modules.appointments.domain.entities import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
)


def type_row_to_entity(row: AppointmentTypeRow) -> AppointmentType:
    return AppointmentType(
        id=row.id,
        name=row.name,
        duration=timedelta(minutes=row.duration_minutes),
        price=Decimal(row.price),
        is_emergency=row.is_emergency,
        is_active=row.is_active,
    )


def type_entity_to_row(appointment_type: AppointmentType) -> AppointmentTypeRow:
    return AppointmentTypeRow(
        name=appointment_type.name,
        duration_minutes=int(appointment_type.duration.total_seconds() // 60),
        price=appointment_type.price,
        is_emergency=appointment_type.is_emergency,
        is_active=appointment_type.is_active,
    )


def row_to_entity(row: AppointmentRow) -> Appointment:
    return Appointment(
        id=row.id,
        scheduled_at=as_utc(row.scheduled_at),
        duration=timedelta(minutes=row.duration_minutes),
        client_id=row.client_id,
        pet_id=row.pet_id,
        veterinarian_id=row.veterinarian_id,
        appointment_type_id=row.appointment_type_id,
        description=row.description,
        status=AppointmentStatus(row.status),
        cancellation_reason=row.cancellation_reason,
        updated_by=row.updated_by,
        reminder_sent_at=as_utc(row.reminder_sent_at) if row.reminder_sent_at else None,
        created_at=as_utc(row.created_at),
    )


def entity_to_row(appointment: Appointment) -> AppointmentRow:
    return AppointmentRow(
        scheduled_at=appointment.scheduled_at,
        duration_minutes=int(appointment.duration.total_seconds() // 60),
        client_id=appointment.client_id,
        pet_id=appointment.pet_id,
        veterinarian_id=appointment.veterinarian_id,
        appointment_type_id=appointment.appointment_type_id,
        description=appointment.description,
        status=appointment.status.value,
        cancellation_reason=appointment.cancellation_reason,
        updated_by=appointment.updated_by,
        reminder_sent_at=appointment.reminder_sent_at,
        created_at=appointment.created_at,
    )

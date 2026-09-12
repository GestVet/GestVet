"""Lectores hacia datos que poseen otros módulos.

El panel de indicadores no es dueño de ningún dato: lee, cruza y resume lo
que `pets`, `medical_records`, `appointments`, `billing`, `reviews` y
`complaints` ya registraron. Consultas crudas contra tablas ajenas, igual que
hacen los lectores de todos los demás módulos hacia esas mismas tablas.

Las columnas de fecha se declaran con `.columns(...)` porque, sin eso, una
consulta cruda le llega a SQLite como texto plano en vez de `datetime`: el
motor no sabe que esa columna es una fecha si la consulta no pasó por el
sistema de tipos de SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import DateTime, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.core.timestamps import as_utc
from gestvet.modules.insights.ports.appointment_directory import AppointmentRecord
from gestvet.modules.insights.ports.billing_directory import PaymentRecord
from gestvet.modules.insights.ports.clinical_directory import PetCareRecord
from gestvet.modules.insights.ports.reputation_directory import VeterinarianSignal

_MOMENT = DateTime(timezone=True)
_CENTS = Decimal("0.01")

_CARE_RECORDS = text(
    "SELECT pets.id AS pet_id, pets.name AS pet_name, pets.owner_id, "
    "users.first_name, users.last_name, pets.created_at AS registered_at, "
    "MAX(CASE WHEN clinical_entries.kind = 'vaccine' "
    "THEN clinical_entries.occurred_at END) AS last_vaccine_at, "
    "MAX(CASE WHEN clinical_entries.kind IN ('consultation', 'follow_up') "
    "THEN clinical_entries.occurred_at END) AS last_checkup_at "
    "FROM pets "
    "JOIN users ON users.id = pets.owner_id "
    "LEFT JOIN clinical_entries ON clinical_entries.pet_id = pets.id "
    "WHERE pets.is_active "
    "GROUP BY pets.id, pets.name, pets.owner_id, users.first_name, users.last_name, "
    "pets.created_at"
).columns(
    registered_at=_MOMENT,
    last_vaccine_at=_MOMENT,
    last_checkup_at=_MOMENT,
)

_APPOINTMENT_RECORDS = (
    text(
        "SELECT appointments.id AS appointment_id, appointments.client_id, "
        "users.first_name, users.last_name, pets.name AS pet_name, "
        "appointments.scheduled_at, appointments.duration_minutes, appointments.status "
        "FROM appointments "
        "JOIN users ON users.id = appointments.client_id "
        "JOIN pets ON pets.id = appointments.pet_id "
        "WHERE appointments.scheduled_at BETWEEN :since AND :until"
    )
    .columns(scheduled_at=_MOMENT)
    .bindparams(
        bindparam("since", type_=_MOMENT),
        bindparam("until", type_=_MOMENT),
    )
)

_PAYMENT_RECORDS = (
    text(
        "SELECT payments.id AS payment_id, payments.appointment_id, payments.client_id, "
        "payments.amount, payments.paid_at, "
        "appointment_types.id AS appointment_type_id, appointment_types.name AS type_label, "
        "appointment_types.is_emergency "
        "FROM payments "
        "JOIN appointments ON appointments.id = payments.appointment_id "
        "JOIN appointment_types ON appointment_types.id = appointments.appointment_type_id "
        "WHERE payments.voided_at IS NULL AND payments.paid_at >= :since"
    )
    .columns(paid_at=_MOMENT)
    .bindparams(bindparam("since", type_=_MOMENT))
)

_LOW_RATING_COUNTS = text(
    "SELECT veterinarian_id, COUNT(*) AS total FROM reviews "
    "WHERE rating <= 2 AND created_at >= :since GROUP BY veterinarian_id"
).bindparams(bindparam("since", type_=_MOMENT))

_COMPLAINT_COUNTS = text(
    "SELECT veterinarian_id, COUNT(*) AS total FROM complaints "
    "WHERE created_at >= :since GROUP BY veterinarian_id"
).bindparams(bindparam("since", type_=_MOMENT))

_ACTIVE_VETERINARIANS = text(
    "SELECT id, first_name, last_name FROM users "
    "WHERE role IN (:vet_role, :emergency_role) AND is_active"
)


class SqlClinicalDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def care_records(self) -> list[PetCareRecord]:
        rows = await self._session.execute(_CARE_RECORDS)
        return [
            PetCareRecord(
                pet_id=row.pet_id,
                pet_name=row.pet_name,
                owner_id=row.owner_id,
                owner_name=f"{row.first_name} {row.last_name}".strip(),
                registered_at=as_utc(row.registered_at),
                last_vaccine_at=as_utc(row.last_vaccine_at) if row.last_vaccine_at else None,
                last_checkup_at=as_utc(row.last_checkup_at) if row.last_checkup_at else None,
            )
            for row in rows
        ]


class SqlAppointmentDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def recent_and_upcoming(
        self, since: datetime, until: datetime
    ) -> list[AppointmentRecord]:
        rows = await self._session.execute(_APPOINTMENT_RECORDS, {"since": since, "until": until})
        return [
            AppointmentRecord(
                appointment_id=row.appointment_id,
                client_id=row.client_id,
                client_name=f"{row.first_name} {row.last_name}".strip(),
                pet_name=row.pet_name,
                scheduled_at=as_utc(row.scheduled_at),
                ends_at=as_utc(row.scheduled_at + timedelta(minutes=row.duration_minutes)),
                status=row.status,
            )
            for row in rows
        ]


class SqlBillingDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def payments_since(self, since: datetime) -> list[PaymentRecord]:
        rows = await self._session.execute(_PAYMENT_RECORDS, {"since": since})
        return [
            PaymentRecord(
                payment_id=row.payment_id,
                appointment_id=row.appointment_id,
                client_id=row.client_id,
                appointment_type_id=row.appointment_type_id,
                appointment_type_label=row.type_label,
                is_emergency_type=bool(row.is_emergency),
                amount=Decimal(str(row.amount)).quantize(_CENTS),
                paid_at=as_utc(row.paid_at),
            )
            for row in rows
        ]


class SqlReputationDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def signals_since(self, since: datetime) -> list[VeterinarianSignal]:
        low_ratings = {
            row.veterinarian_id: row.total
            for row in await self._session.execute(_LOW_RATING_COUNTS, {"since": since})
        }
        complaints = {
            row.veterinarian_id: row.total
            for row in await self._session.execute(_COMPLAINT_COUNTS, {"since": since})
        }
        veterinarians = await self._session.execute(
            _ACTIVE_VETERINARIANS,
            {
                "vet_role": Role.VETERINARIAN.value,
                "emergency_role": Role.EMERGENCY_VETERINARIAN.value,
            },
        )
        return [
            VeterinarianSignal(
                veterinarian_id=row.id,
                veterinarian_name=f"{row.first_name} {row.last_name}".strip(),
                low_rating_count=low_ratings.get(row.id, 0),
                complaint_count=complaints.get(row.id, 0),
            )
            for row in veterinarians
        ]

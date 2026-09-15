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

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.core.timestamps import as_utc
from gestvet.modules.insights.ports.appointment_directory import AppointmentRecord
from gestvet.modules.insights.ports.billing_directory import PaymentRecord
from gestvet.modules.insights.ports.clinical_directory import PetCareRecord
from gestvet.modules.insights.ports.pet_overview_directory import PetOverviewRecord
from gestvet.modules.insights.ports.reputation_directory import VeterinarianSignal
from gestvet.modules.insights.ports.service_consumption_directory import (
    ServiceConsumptionRecord,
)

_MOMENT = DateTime(timezone=True)
_DAY = Date()
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
        "appointment_types.is_emergency, users.first_name, users.last_name, "
        "pets.name AS pet_name "
        "FROM payments "
        "JOIN appointments ON appointments.id = payments.appointment_id "
        "JOIN users ON users.id = payments.client_id "
        "JOIN pets ON pets.id = appointments.pet_id "
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
    "SELECT id, first_name, last_name FROM users WHERE role = :vet_role AND is_active"
)

_PET_OVERVIEW_BASE = (
    "SELECT pets.id AS pet_id, pets.name AS pet_name, pets.owner_id, "
    "users.first_name, users.last_name, pets.species, pets.breed, pets.sex, "
    "pets.birth_date, pets.weight_kg, pets.is_active, "
    "MAX(pet_vaccinations.applied_on) AS last_vaccine_on, "
    "MIN(pet_vaccinations.next_due_on) AS next_vaccine_due_on, "
    "COUNT(pet_vaccinations.id) AS vaccine_count "
    "FROM pets "
    "JOIN users ON users.id = pets.owner_id "
    "LEFT JOIN pet_vaccinations ON pet_vaccinations.pet_id = pets.id "
    "{filter} "
    "GROUP BY pets.id, pets.name, pets.owner_id, users.first_name, users.last_name, "
    "pets.species, pets.breed, pets.sex, pets.birth_date, pets.weight_kg, pets.is_active"
)

_PET_OVERVIEW_RECORDS = text(_PET_OVERVIEW_BASE.format(filter="")).columns(
    birth_date=_DAY,
    last_vaccine_on=_DAY,
    next_vaccine_due_on=_DAY,
)

# Sin filtro, "todo el tiempo": evita tener una tercera variante de la
# consulta solo para el caso sin rango de fechas (el filtro de estado sí
# tiene su propia variante, ver mas abajo).
_FAR_PAST = datetime(2000, 1, 1, tzinfo=UTC)
_FAR_FUTURE = datetime(2100, 1, 1, tzinfo=UTC)

_SERVICE_CONSUMPTION_BASE = (
    "SELECT appointment_types.id AS appointment_type_id, appointment_types.name, "
    "appointment_types.is_emergency, appointment_types.price, "
    "COUNT(appointments.id) AS appointment_count "
    "FROM appointment_types "
    "LEFT JOIN appointments ON appointments.appointment_type_id = appointment_types.id "
    "AND appointments.scheduled_at BETWEEN :since AND :until{status_filter} "
    "GROUP BY appointment_types.id, appointment_types.name, appointment_types.is_emergency, "
    "appointment_types.price "
    "ORDER BY appointment_count DESC"
)

_SERVICE_CONSUMPTION_RECORDS = (
    text(_SERVICE_CONSUMPTION_BASE.format(status_filter=""))
    .columns(price=Numeric(10, 2))
    .bindparams(bindparam("since", type_=_MOMENT), bindparam("until", type_=_MOMENT))
)

_SERVICE_CONSUMPTION_RECORDS_BY_STATUS = (
    text(_SERVICE_CONSUMPTION_BASE.format(status_filter=" AND appointments.status = :status"))
    .columns(price=Numeric(10, 2))
    .bindparams(
        bindparam("since", type_=_MOMENT),
        bindparam("until", type_=_MOMENT),
        bindparam("status"),
    )
)

_PET_OVERVIEW_RECORDS_FOR_VET = (
    text(
        _PET_OVERVIEW_BASE.format(
            filter=(
                "WHERE EXISTS (SELECT 1 FROM clinical_entries "
                "WHERE clinical_entries.pet_id = pets.id "
                "AND clinical_entries.veterinarian_id = :vet_id) "
                "OR EXISTS (SELECT 1 FROM pet_vaccinations AS v "
                "WHERE v.pet_id = pets.id AND v.veterinarian_id = :vet_id)"
            )
        )
    )
    .columns(birth_date=_DAY, last_vaccine_on=_DAY, next_vaccine_due_on=_DAY)
    .bindparams(bindparam("vet_id"))
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


class SqlPetOverviewDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def records(self, veterinarian_id: int | None) -> list[PetOverviewRecord]:
        if veterinarian_id is None:
            rows = await self._session.execute(_PET_OVERVIEW_RECORDS)
        else:
            rows = await self._session.execute(
                _PET_OVERVIEW_RECORDS_FOR_VET, {"vet_id": veterinarian_id}
            )
        return [
            PetOverviewRecord(
                pet_id=row.pet_id,
                pet_name=row.pet_name,
                owner_id=row.owner_id,
                owner_name=f"{row.first_name} {row.last_name}".strip(),
                species=row.species,
                breed=row.breed,
                sex=row.sex,
                birth_date=row.birth_date,
                weight_kg=row.weight_kg,
                is_active=bool(row.is_active),
                last_vaccine_on=row.last_vaccine_on,
                next_vaccine_due_on=row.next_vaccine_due_on,
                vaccine_count=row.vaccine_count,
            )
            for row in rows
        ]


class SqlServiceConsumptionDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def records(
        self,
        starts_after: datetime | None,
        ends_before: datetime | None,
        status: str | None,
    ) -> list[ServiceConsumptionRecord]:
        params = {
            "since": starts_after or _FAR_PAST,
            "until": ends_before or _FAR_FUTURE,
        }
        if status is None:
            rows = await self._session.execute(_SERVICE_CONSUMPTION_RECORDS, params)
        else:
            rows = await self._session.execute(
                _SERVICE_CONSUMPTION_RECORDS_BY_STATUS, {**params, "status": status}
            )
        return [
            ServiceConsumptionRecord(
                appointment_type_id=row.appointment_type_id,
                name=row.name,
                is_emergency=bool(row.is_emergency),
                price=row.price,
                appointment_count=row.appointment_count,
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
                client_name=f"{row.first_name} {row.last_name}".strip(),
                pet_name=row.pet_name,
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

"""Reglas puras del panel de indicadores.

Nada de esto llama a IA ni entrena nada: son umbrales y conteos sobre datos
que otros módulos ya registran. Vive separado de las entidades para que cada
regla se pueda probar contra una lista de registros armada a mano, sin tocar
una base de datos.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from gestvet.modules.insights.domain.entities import (
    CARE_CHECKUP_REMINDER_DAYS,
    CARE_VACCINE_REMINDER_DAYS,
    NO_SHOW_RISK_THRESHOLD,
    NO_SHOW_STALE_GRACE_HOURS,
    OVERVIEW_DUE_SOON_DAYS,
    PAYMENT_ANOMALY_DEVIATION,
    PAYMENT_ANOMALY_MIN_SAMPLES,
    VETERINARIAN_ALERT_COMPLAINT_THRESHOLD,
    VETERINARIAN_ALERT_LOW_RATING_THRESHOLD,
    AppointmentRecord,
    CareReminder,
    NoShowRisk,
    PaymentAnomaly,
    PaymentRecord,
    PetCareRecord,
    PetOverview,
    PetOverviewRecord,
    ServiceConsumption,
    ServiceConsumptionRecord,
    VaccinationStatus,
    VeterinarianAlert,
    VeterinarianSignal,
)

_ACTIVE_STATUSES = frozenset({"pending", "confirmed"})


def build_care_reminders(records: list[PetCareRecord], now: datetime) -> list[CareReminder]:
    reminders: list[CareReminder] = []
    for record in records:
        vaccine_since = record.last_vaccine_at or record.registered_at
        if now - vaccine_since > timedelta(days=CARE_VACCINE_REMINDER_DAYS):
            reminders.append(_reminder(record, "vacuna", record.last_vaccine_at))

        checkup_since = record.last_checkup_at or record.registered_at
        if now - checkup_since > timedelta(days=CARE_CHECKUP_REMINDER_DAYS):
            reminders.append(_reminder(record, "control", record.last_checkup_at))
    return reminders


def _reminder(
    record: PetCareRecord, reason: str, last_occurred_at: datetime | None
) -> CareReminder:
    return CareReminder(
        pet_id=record.pet_id,
        pet_name=record.pet_name,
        owner_id=record.owner_id,
        owner_name=record.owner_name,
        reason=reason,
        last_occurred_at=last_occurred_at,
    )


def build_no_show_risks(records: list[AppointmentRecord], now: datetime) -> list[NoShowRisk]:
    grace = timedelta(hours=NO_SHOW_STALE_GRACE_HOURS)
    incidents_by_client: dict[int, int] = {}
    upcoming: list[AppointmentRecord] = []

    for record in records:
        if record.status not in _ACTIVE_STATUSES:
            continue
        if record.ends_at + grace < now:
            incidents_by_client[record.client_id] = incidents_by_client.get(record.client_id, 0) + 1
        elif record.scheduled_at > now:
            upcoming.append(record)

    risks = [
        NoShowRisk(
            appointment_id=record.appointment_id,
            client_id=record.client_id,
            client_name=record.client_name,
            pet_name=record.pet_name,
            scheduled_at=record.scheduled_at,
            past_incidents=incidents_by_client[record.client_id],
        )
        for record in upcoming
        if incidents_by_client.get(record.client_id, 0) >= NO_SHOW_RISK_THRESHOLD
    ]
    return sorted(risks, key=lambda risk: risk.scheduled_at)


def build_payment_anomalies(records: list[PaymentRecord]) -> list[PaymentAnomaly]:
    # Una emergencia no tiene un monto "típico" por diseño: el precio se
    # calcula al final de la atención y puede variar mucho sin que eso sea
    # una anomalía. Ver `billing.use_cases.create_qr_charge`, que aplica la
    # misma exclusión.
    candidates = [record for record in records if not record.is_emergency_type]

    amounts_by_type: dict[int, list[PaymentRecord]] = {}
    for record in candidates:
        amounts_by_type.setdefault(record.appointment_type_id, []).append(record)

    typical_by_type = {
        type_id: sum((r.amount for r in group), Decimal("0")) / len(group)
        for type_id, group in amounts_by_type.items()
        if len(group) >= PAYMENT_ANOMALY_MIN_SAMPLES
    }

    anomalies: list[PaymentAnomaly] = []
    for record in candidates:
        typical = typical_by_type.get(record.appointment_type_id)
        if typical is None or typical == 0:
            continue
        deviation = abs(record.amount - typical) / typical
        if deviation > PAYMENT_ANOMALY_DEVIATION:
            anomalies.append(
                PaymentAnomaly(
                    payment_id=record.payment_id,
                    appointment_id=record.appointment_id,
                    client_id=record.client_id,
                    appointment_type_label=record.appointment_type_label,
                    amount=record.amount,
                    typical_amount=typical,
                    paid_at=record.paid_at,
                    client_name=record.client_name,
                    pet_name=record.pet_name,
                )
            )
    return sorted(anomalies, key=lambda anomaly: anomaly.paid_at, reverse=True)


def _age_in_years(birth_date: date, today: date) -> int:
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return max(years, 0)


def vaccination_status(record: PetOverviewRecord, today: date) -> VaccinationStatus:
    if record.vaccine_count == 0:
        return "no_vaccines"
    if record.next_vaccine_due_on is None:
        return "up_to_date"
    if record.next_vaccine_due_on < today:
        return "overdue"
    if (record.next_vaccine_due_on - today).days <= OVERVIEW_DUE_SOON_DAYS:
        return "due_soon"
    return "up_to_date"


def build_pet_overview(records: list[PetOverviewRecord], today: date) -> list[PetOverview]:
    return [
        PetOverview(
            pet_id=record.pet_id,
            pet_name=record.pet_name,
            owner_name=record.owner_name,
            species=record.species,
            breed=record.breed,
            sex=record.sex,
            age_years=_age_in_years(record.birth_date, today),
            weight_kg=record.weight_kg,
            is_active=record.is_active,
            vaccination_status=vaccination_status(record, today),
        )
        for record in records
    ]


def build_service_consumption(
    records: list[ServiceConsumptionRecord],
) -> list[ServiceConsumption]:
    items = [
        ServiceConsumption(
            appointment_type_id=record.appointment_type_id,
            name=record.name,
            is_emergency=record.is_emergency,
            price=record.price,
            appointment_count=record.appointment_count,
            estimated_revenue=record.price * record.appointment_count,
        )
        for record in records
    ]
    return sorted(items, key=lambda item: item.appointment_count, reverse=True)


def build_veterinarian_alerts(signals: list[VeterinarianSignal]) -> list[VeterinarianAlert]:
    return [
        VeterinarianAlert(
            veterinarian_id=signal.veterinarian_id,
            veterinarian_name=signal.veterinarian_name,
            low_rating_count=signal.low_rating_count,
            complaint_count=signal.complaint_count,
        )
        for signal in signals
        if signal.low_rating_count >= VETERINARIAN_ALERT_LOW_RATING_THRESHOLD
        or signal.complaint_count >= VETERINARIAN_ALERT_COMPLAINT_THRESHOLD
    ]

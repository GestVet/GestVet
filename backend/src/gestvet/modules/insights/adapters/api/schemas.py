"""Contrato HTTP del panel de indicadores."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from gestvet.modules.insights.domain.entities import (
    CareReminder,
    NoShowRisk,
    PaymentAnomaly,
    VeterinarianAlert,
)

_REASON_LABELS = {"vacuna": "Vacuna vencida", "control": "Control vencido"}
_CENTS = Decimal("0.01")


class CareReminderResponse(BaseModel):
    pet_id: int
    pet_name: str
    owner_id: int
    owner_name: str
    reason_label: str
    last_occurred_at: datetime | None

    @classmethod
    def from_entity(cls, reminder: CareReminder) -> CareReminderResponse:
        return cls(
            pet_id=reminder.pet_id,
            pet_name=reminder.pet_name,
            owner_id=reminder.owner_id,
            owner_name=reminder.owner_name,
            reason_label=_REASON_LABELS[reminder.reason],
            last_occurred_at=reminder.last_occurred_at,
        )


class CareReminderListResponse(BaseModel):
    items: list[CareReminderResponse]


class NoShowRiskResponse(BaseModel):
    appointment_id: int
    client_id: int
    client_name: str
    pet_name: str
    scheduled_at: datetime
    past_incidents: int

    @classmethod
    def from_entity(cls, risk: NoShowRisk) -> NoShowRiskResponse:
        return cls(
            appointment_id=risk.appointment_id,
            client_id=risk.client_id,
            client_name=risk.client_name,
            pet_name=risk.pet_name,
            scheduled_at=risk.scheduled_at,
            past_incidents=risk.past_incidents,
        )


class NoShowRiskListResponse(BaseModel):
    items: list[NoShowRiskResponse]


class PaymentAnomalyResponse(BaseModel):
    payment_id: int
    appointment_id: int
    client_id: int
    appointment_type_label: str
    amount: Decimal
    typical_amount: Decimal
    paid_at: datetime

    @classmethod
    def from_entity(cls, anomaly: PaymentAnomaly) -> PaymentAnomalyResponse:
        return cls(
            payment_id=anomaly.payment_id,
            appointment_id=anomaly.appointment_id,
            client_id=anomaly.client_id,
            appointment_type_label=anomaly.appointment_type_label,
            amount=anomaly.amount,
            typical_amount=anomaly.typical_amount.quantize(_CENTS),
            paid_at=anomaly.paid_at,
        )


class PaymentAnomalyListResponse(BaseModel):
    items: list[PaymentAnomalyResponse]


class VeterinarianAlertResponse(BaseModel):
    veterinarian_id: int
    veterinarian_name: str
    low_rating_count: int
    complaint_count: int

    @classmethod
    def from_entity(cls, alert: VeterinarianAlert) -> VeterinarianAlertResponse:
        return cls(
            veterinarian_id=alert.veterinarian_id,
            veterinarian_name=alert.veterinarian_name,
            low_rating_count=alert.low_rating_count,
            complaint_count=alert.complaint_count,
        )


class VeterinarianAlertListResponse(BaseModel):
    items: list[VeterinarianAlertResponse]

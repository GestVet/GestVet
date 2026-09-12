"""Adaptador de entrada HTTP del panel de indicadores.

Todo el módulo es de solo lectura y solo para administración: son señales de
negocio (ingresos, desempeño de veterinarios) que no le corresponden a un
cliente, y que tampoco hace falta repartir entre todo el personal.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from gestvet.core.auth import require_roles
from gestvet.core.identity import Role
from gestvet.modules.insights.adapters.api.dependencies import (
    AppointmentDirectoryDep,
    BillingDirectoryDep,
    ClinicalDirectoryDep,
    ReputationDirectoryDep,
)
from gestvet.modules.insights.adapters.api.schemas import (
    CareReminderListResponse,
    CareReminderResponse,
    NoShowRiskListResponse,
    NoShowRiskResponse,
    PaymentAnomalyListResponse,
    PaymentAnomalyResponse,
    VeterinarianAlertListResponse,
    VeterinarianAlertResponse,
)
from gestvet.modules.insights.use_cases.list_care_reminders import ListCareReminders
from gestvet.modules.insights.use_cases.list_no_show_risks import ListNoShowRisks
from gestvet.modules.insights.use_cases.list_payment_anomalies import ListPaymentAnomalies
from gestvet.modules.insights.use_cases.list_veterinarian_alerts import ListVeterinarianAlerts

router = APIRouter(dependencies=[Depends(require_roles(Role.ADMIN))])


@router.get(
    "/care-reminders",
    response_model=CareReminderListResponse,
    summary="Mascotas con vacuna o control vencido",
)
async def list_care_reminders(clinical: ClinicalDirectoryDep) -> CareReminderListResponse:
    reminders = await ListCareReminders(clinical)()
    return CareReminderListResponse(
        items=[CareReminderResponse.from_entity(item) for item in reminders]
    )


@router.get(
    "/no-show-risks",
    response_model=NoShowRiskListResponse,
    summary="Citas próximas con riesgo de inasistencia",
)
async def list_no_show_risks(appointments: AppointmentDirectoryDep) -> NoShowRiskListResponse:
    risks = await ListNoShowRisks(appointments)()
    return NoShowRiskListResponse(items=[NoShowRiskResponse.from_entity(item) for item in risks])


@router.get(
    "/payment-anomalies",
    response_model=PaymentAnomalyListResponse,
    summary="Pagos cuyo monto se aleja del típico de su tipo de cita",
)
async def list_payment_anomalies(billing: BillingDirectoryDep) -> PaymentAnomalyListResponse:
    anomalies = await ListPaymentAnomalies(billing)()
    return PaymentAnomalyListResponse(
        items=[PaymentAnomalyResponse.from_entity(item) for item in anomalies]
    )


@router.get(
    "/veterinarian-alerts",
    response_model=VeterinarianAlertListResponse,
    summary="Veterinarios con reseñas bajas o reclamos recientes",
)
async def list_veterinarian_alerts(
    reputation: ReputationDirectoryDep,
) -> VeterinarianAlertListResponse:
    alerts = await ListVeterinarianAlerts(reputation)()
    return VeterinarianAlertListResponse(
        items=[VeterinarianAlertResponse.from_entity(item) for item in alerts]
    )

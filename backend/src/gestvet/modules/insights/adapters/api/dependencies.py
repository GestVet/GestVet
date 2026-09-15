from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.insights.adapters.persistence.directories import (
    SqlAppointmentDirectory,
    SqlBillingDirectory,
    SqlClinicalDirectory,
    SqlPetOverviewDirectory,
    SqlReputationDirectory,
    SqlServiceConsumptionDirectory,
)
from gestvet.modules.insights.adapters.reports.service_consumption_pdf import (
    ReportLabServiceConsumptionReport,
)
from gestvet.modules.insights.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.insights.ports.billing_directory import BillingDirectory
from gestvet.modules.insights.ports.clinical_directory import ClinicalDirectory
from gestvet.modules.insights.ports.pet_overview_directory import PetOverviewDirectory
from gestvet.modules.insights.ports.reputation_directory import ReputationDirectory
from gestvet.modules.insights.ports.service_consumption_directory import (
    ServiceConsumptionDirectory,
)
from gestvet.modules.insights.ports.service_consumption_report import (
    ServiceConsumptionRenderer,
)


def get_clinical_directory(session: SessionDep) -> ClinicalDirectory:
    return SqlClinicalDirectory(session)


def get_pet_overview_directory(session: SessionDep) -> PetOverviewDirectory:
    return SqlPetOverviewDirectory(session)


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


def get_billing_directory(session: SessionDep) -> BillingDirectory:
    return SqlBillingDirectory(session)


def get_reputation_directory(session: SessionDep) -> ReputationDirectory:
    return SqlReputationDirectory(session)


def get_service_consumption_directory(session: SessionDep) -> ServiceConsumptionDirectory:
    return SqlServiceConsumptionDirectory(session)


def get_service_consumption_renderer() -> ServiceConsumptionRenderer:
    return ReportLabServiceConsumptionReport()


ClinicalDirectoryDep = Annotated[ClinicalDirectory, Depends(get_clinical_directory)]
PetOverviewDirectoryDep = Annotated[PetOverviewDirectory, Depends(get_pet_overview_directory)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]
BillingDirectoryDep = Annotated[BillingDirectory, Depends(get_billing_directory)]
ReputationDirectoryDep = Annotated[ReputationDirectory, Depends(get_reputation_directory)]
ServiceConsumptionDirectoryDep = Annotated[
    ServiceConsumptionDirectory, Depends(get_service_consumption_directory)
]
ServiceConsumptionRendererDep = Annotated[
    ServiceConsumptionRenderer, Depends(get_service_consumption_renderer)
]

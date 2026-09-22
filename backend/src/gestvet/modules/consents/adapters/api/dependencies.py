from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from gestvet.core.auth import SessionDep
from gestvet.modules.consents.adapters.persistence.directories import (
    SqlAppointmentDirectory,
    SqlNameDirectory,
    SqlPetDirectory,
)
from gestvet.modules.consents.adapters.persistence.repositories import (
    SqlAlchemyConsentRepository,
    SqlAlchemyConsentTemplateRepository,
)
from gestvet.modules.consents.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.consents.ports.consent_repository import (
    ConsentRepository,
    ConsentTemplateRepository,
)
from gestvet.modules.consents.ports.name_directory import NameDirectory
from gestvet.modules.consents.ports.pet_directory import PetDirectory
from gestvet.modules.consents.use_cases.signing import RequestOrigin


def get_consent_repository(session: SessionDep) -> ConsentRepository:
    return SqlAlchemyConsentRepository(session)


def get_template_repository(session: SessionDep) -> ConsentTemplateRepository:
    return SqlAlchemyConsentTemplateRepository(session)


def get_pet_directory(session: SessionDep) -> PetDirectory:
    return SqlPetDirectory(session)


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


def get_name_directory(session: SessionDep) -> NameDirectory:
    return SqlNameDirectory(session)


def get_request_origin(request: Request) -> RequestOrigin:
    # La dirección es la del par TCP. Detrás de un proxy hay que arrancar
    # uvicorn con `--proxy-headers` para que sea la del navegador y no la
    # del proxy; leer `X-Forwarded-For` a mano dejaría que cualquiera la
    # inventara.
    return RequestOrigin(
        ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )


ConsentRepositoryDep = Annotated[ConsentRepository, Depends(get_consent_repository)]
TemplateRepositoryDep = Annotated[ConsentTemplateRepository, Depends(get_template_repository)]
PetDirectoryDep = Annotated[PetDirectory, Depends(get_pet_directory)]
RequestOriginDep = Annotated[RequestOrigin, Depends(get_request_origin)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]
NameDirectoryDep = Annotated[NameDirectory, Depends(get_name_directory)]

"""Adaptador de entrada HTTP para los consentimientos que pide el veterinario.

Pedir, tomar la firma en persona y atender sin consentimiento por urgencia
vital exigen `consents.request`: son actos del veterinario que atiende.
Aceptar o rechazar en línea exige `consents.respond`, y el caso de uso lo
acota a los pedidos del propio cliente.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal
from gestvet.core.permissions import Permission
from gestvet.core.realtime_broker import EventPublisherDep
from gestvet.modules.consents.adapters.api.dependencies import (
    AppointmentDirectoryDep,
    ConsentRepositoryDep,
    NameDirectoryDep,
    RequestOriginDep,
    TemplateRepositoryDep,
)
from gestvet.modules.consents.adapters.api.responses import http_error, notify, response_for
from gestvet.modules.consents.adapters.api.schemas import (
    AcceptConsentRequest,
    ConsentResponse,
    DeclineConsentRequest,
    RequestConsentRequest,
    WaiveConsentRequest,
)
from gestvet.modules.consents.domain.exceptions import ConsentsError
from gestvet.modules.consents.use_cases.accept_consent_in_person import (
    AcceptConsentInPerson,
    AcceptConsentInPersonCommand,
)
from gestvet.modules.consents.use_cases.request_consent import (
    RequestConsent,
    RequestConsentCommand,
)
from gestvet.modules.consents.use_cases.respond_to_consent import (
    AcceptConsent,
    AcceptConsentCommand,
    DeclineConsent,
    DeclineConsentCommand,
)
from gestvet.modules.consents.use_cases.waive_consent import WaiveConsent, WaiveConsentCommand

router = APIRouter()

VeterinarianDep = Annotated[Principal, Depends(require_permission(Permission.CONSENTS_REQUEST))]
OwnerDep = Annotated[Principal, Depends(require_permission(Permission.CONSENTS_RESPOND))]


@router.post(
    "",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pedir un consentimiento específico sobre una cita",
)
async def request_consent(
    payload: RequestConsentRequest,
    veterinarian: VeterinarianDep,
    consents: ConsentRepositoryDep,
    templates: TemplateRepositoryDep,
    appointments: AppointmentDirectoryDep,
    names: NameDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> ConsentResponse:
    try:
        consent = await RequestConsent(consents, templates, appointments, activity)(
            RequestConsentCommand(
                requester=veterinarian,
                appointment_id=payload.appointment_id,
                kind=payload.kind,
                procedure=payload.details.procedure,
                prognosis=payload.details.prognosis,
                estimated_cost=payload.details.estimated_cost,
                notes=payload.details.notes,
            )
        )
    except ConsentsError as error:
        raise http_error(error) from error
    notify(events, consent)
    return await response_for(consent, names)


@router.post(
    "/waive",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la atención sin consentimiento por urgencia vital",
)
async def waive_consent(
    payload: WaiveConsentRequest,
    veterinarian: VeterinarianDep,
    consents: ConsentRepositoryDep,
    templates: TemplateRepositoryDep,
    appointments: AppointmentDirectoryDep,
    names: NameDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> ConsentResponse:
    try:
        consent = await WaiveConsent(consents, templates, appointments, activity)(
            WaiveConsentCommand(
                veterinarian=veterinarian,
                appointment_id=payload.appointment_id,
                kind=payload.kind,
                justification=payload.justification,
            )
        )
    except ConsentsError as error:
        raise http_error(error) from error
    notify(events, consent)
    return await response_for(consent, names)


@router.post(
    "/{consent_id}/accept",
    response_model=ConsentResponse,
    summary="Aceptar en línea un consentimiento pedido",
)
async def accept_consent(
    consent_id: int,
    payload: AcceptConsentRequest,
    owner: OwnerDep,
    consents: ConsentRepositoryDep,
    names: NameDirectoryDep,
    origin: RequestOriginDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> ConsentResponse:
    try:
        consent = await AcceptConsent(consents, activity)(
            AcceptConsentCommand(
                consent_id=consent_id,
                client_id=owner.user_id,
                signer_name=payload.signer_name,
                origin=origin,
            )
        )
    except ConsentsError as error:
        raise http_error(error) from error
    notify(events, consent)
    return await response_for(consent, names)


@router.post(
    "/{consent_id}/decline",
    response_model=ConsentResponse,
    summary="Rechazar un consentimiento pedido",
)
async def decline_consent(
    consent_id: int,
    payload: DeclineConsentRequest,
    owner: OwnerDep,
    consents: ConsentRepositoryDep,
    names: NameDirectoryDep,
    origin: RequestOriginDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> ConsentResponse:
    try:
        consent = await DeclineConsent(consents, activity)(
            DeclineConsentCommand(
                consent_id=consent_id,
                client_id=owner.user_id,
                reason=payload.reason,
                origin=origin,
            )
        )
    except ConsentsError as error:
        raise http_error(error) from error
    notify(events, consent)
    return await response_for(consent, names)


@router.post(
    "/{consent_id}/accept-in-person",
    response_model=ConsentResponse,
    summary="Registrar que el responsable firmó el pedido en presencia del veterinario",
)
async def accept_consent_in_person(
    consent_id: int,
    payload: AcceptConsentRequest,
    veterinarian: VeterinarianDep,
    consents: ConsentRepositoryDep,
    appointments: AppointmentDirectoryDep,
    names: NameDirectoryDep,
    origin: RequestOriginDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> ConsentResponse:
    try:
        consent = await AcceptConsentInPerson(consents, appointments, activity)(
            AcceptConsentInPersonCommand(
                consent_id=consent_id,
                witness=veterinarian,
                signer_name=payload.signer_name,
                origin=origin,
            )
        )
    except ConsentsError as error:
        raise http_error(error) from error
    notify(events, consent)
    return await response_for(consent, names)

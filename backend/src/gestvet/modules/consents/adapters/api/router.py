"""Adaptador de entrada HTTP para consentimientos informados: lectura y riesgo de emergencia.

El riesgo de emergencia usa los mismos permisos que abrir una emergencia:
quien puede abrirla puede firmar lo que la habilita. Los pedidos del
veterinario tienen permisos propios y viven en `requests_router`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal
from gestvet.core.permissions import Permission
from gestvet.modules.consents.adapters.api.dependencies import (
    AppointmentDirectoryDep,
    ConsentRepositoryDep,
    NameDirectoryDep,
    PetDirectoryDep,
    RequestOriginDep,
    TemplateRepositoryDep,
)
from gestvet.modules.consents.adapters.api.responses import (
    http_error,
    response_for,
    responses_for,
)
from gestvet.modules.consents.adapters.api.schemas import (
    AcceptEmergencyRiskRequest,
    ConsentListResponse,
    ConsentResponse,
    ConsentTemplateResponse,
    RecordInPersonEmergencyRiskRequest,
)
from gestvet.modules.consents.domain.entities import ConsentKind, ConsentStatus
from gestvet.modules.consents.domain.exceptions import ConsentsError
from gestvet.modules.consents.use_cases.accept_emergency_risk import (
    AcceptEmergencyRisk,
    AcceptEmergencyRiskCommand,
)
from gestvet.modules.consents.use_cases.read_consents import (
    ConsentQuery,
    GetConsent,
    GetCurrentTemplate,
    ListConsents,
)
from gestvet.modules.consents.use_cases.record_in_person_emergency_risk import (
    RecordInPersonEmergencyRisk,
    RecordInPersonEmergencyRiskCommand,
)

router = APIRouter()

SignerDep = Annotated[Principal, Depends(require_permission(Permission.EMERGENCIES_OPEN))]
WitnessDep = Annotated[Principal, Depends(require_permission(Permission.EMERGENCIES_OPEN_WALK_IN))]
TemplateReaderDep = Annotated[
    Principal,
    Depends(
        require_permission(
            Permission.EMERGENCIES_OPEN,
            Permission.EMERGENCIES_OPEN_WALK_IN,
            Permission.CONSENTS_REQUEST,
        )
    ),
]
ReaderDep = Annotated[Principal, Depends(require_permission(Permission.APPOINTMENTS_READ))]


@router.get(
    "/templates/current",
    response_model=ConsentTemplateResponse,
    summary="Texto vigente de un tipo de consentimiento",
)
async def current_template(
    principal: TemplateReaderDep,
    templates: TemplateRepositoryDep,
    kind: Annotated[ConsentKind, Query()] = ConsentKind.EMERGENCY_RISK,
) -> ConsentTemplateResponse:
    try:
        template = await GetCurrentTemplate(templates)(kind)
    except ConsentsError as error:
        raise http_error(error) from error
    return ConsentTemplateResponse.from_entity(template)


@router.post(
    "/emergency-risk",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aceptar en línea el riesgo de una emergencia",
)
async def accept_emergency_risk(
    payload: AcceptEmergencyRiskRequest,
    client: SignerDep,
    consents: ConsentRepositoryDep,
    templates: TemplateRepositoryDep,
    pets: PetDirectoryDep,
    origin: RequestOriginDep,
    activity: ActivityRecorderDep,
) -> ConsentResponse:
    try:
        consent = await AcceptEmergencyRisk(consents, templates, pets, activity)(
            AcceptEmergencyRiskCommand(
                client_id=client.user_id,
                pet_id=payload.pet_id,
                template_id=payload.template_id,
                signer_name=payload.signer_name,
                origin=origin,
            )
        )
    except ConsentsError as error:
        raise http_error(error) from error
    return ConsentResponse.from_entity(consent)


@router.post(
    "/emergency-risk/in-person",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar en el mostrador que el responsable aceptó el riesgo",
)
async def record_in_person_emergency_risk(
    payload: RecordInPersonEmergencyRiskRequest,
    staff: WitnessDep,
    consents: ConsentRepositoryDep,
    templates: TemplateRepositoryDep,
    pets: PetDirectoryDep,
    origin: RequestOriginDep,
    activity: ActivityRecorderDep,
) -> ConsentResponse:
    try:
        consent = await RecordInPersonEmergencyRisk(consents, templates, pets, activity)(
            RecordInPersonEmergencyRiskCommand(
                staff_id=staff.user_id,
                client_id=payload.client_id,
                pet_id=payload.pet_id,
                template_id=payload.template_id,
                signer_name=payload.signer_name,
                origin=origin,
            )
        )
    except ConsentsError as error:
        raise http_error(error) from error
    return ConsentResponse.from_entity(consent)


@router.get(
    "", response_model=ConsentListResponse, summary="Consentimientos de una cita o del cliente"
)
async def list_consents(
    principal: ReaderDep,
    consents: ConsentRepositoryDep,
    appointments: AppointmentDirectoryDep,
    names: NameDirectoryDep,
    appointment_id: Annotated[
        int | None, Query(ge=1, description="Cita consultada; obligatoria para el personal")
    ] = None,
    status_filter: Annotated[
        ConsentStatus | None,
        Query(alias="status", description="Estado efectivo: `pending` no trae los vencidos"),
    ] = None,
) -> ConsentListResponse:
    try:
        listado = await ListConsents(consents, appointments)(
            ConsentQuery(appointment_id=appointment_id, status=status_filter), principal
        )
    except ConsentsError as error:
        raise http_error(error) from error
    return ConsentListResponse(
        items=await responses_for(listado.items, names),
        appointment_is_emergency=listado.appointment_is_emergency,
    )


@router.get("/{consent_id}", response_model=ConsentResponse, summary="Ver un consentimiento")
async def get_consent(
    consent_id: int,
    principal: ReaderDep,
    consents: ConsentRepositoryDep,
    names: NameDirectoryDep,
) -> ConsentResponse:
    try:
        consent = await GetConsent(consents)(consent_id, principal)
    except ConsentsError as error:
        raise http_error(error) from error
    return await response_for(consent, names)

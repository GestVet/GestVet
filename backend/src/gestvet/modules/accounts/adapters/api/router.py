"""Adaptador de entrada HTTP para la gestión de clientes.

Traduce peticiones a comandos y errores de dominio a códigos de estado. No
contiene reglas de negocio ni consultas.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal
from gestvet.core.identity_registry import IdentityRegistryUnavailable
from gestvet.core.permissions import Permission
from gestvet.modules.accounts.adapters.api.dependencies import (
    IdentityRegistryDep,
    PasswordHasherDep,
    UserRepositoryDep,
)
from gestvet.modules.accounts.adapters.api.schemas import (
    ClientPageResponse,
    DocumentLookupRequest,
    DocumentLookupResponse,
    RegisterWalkInClientRequest,
    UpdateClientContactRequest,
    UserResponse,
)
from gestvet.modules.accounts.domain.exceptions import (
    DocumentIdRequired,
    DocumentNotFoundInRegistry,
    EmailAlreadyRegistered,
    InvalidDocumentId,
    InvalidEmail,
    UserNotFound,
)
from gestvet.modules.accounts.ports.user_repository import UserQuery
from gestvet.modules.accounts.use_cases.list_clients import CLIENT_ROLES, ListUsers
from gestvet.modules.accounts.use_cases.look_up_document import (
    LookUpDocument,
    LookUpDocumentCommand,
)
from gestvet.modules.accounts.use_cases.manage_accounts import (
    RegisterWalkInClient,
    RegisterWalkInClientCommand,
    UpdateClientContact,
    UpdateClientContactCommand,
)

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# El padrón de clientes es dato personal. Cada endpoint exige un permiso que
# los roles de sistema solo le dan a quien atiende la clínica.
router = APIRouter()

WalkInRegistrarDep = Annotated[
    Principal, Depends(require_permission(Permission.CLIENTS_REGISTER_WALK_IN))
]
ContactEditorDep = Annotated[
    Principal, Depends(require_permission(Permission.CLIENTS_UPDATE_CONTACT))
]


@router.get(
    "",
    response_model=ClientPageResponse,
    dependencies=[Depends(require_permission(Permission.CLIENTS_READ))],
    summary="Listar clientes",
)
async def list_clients(
    users: UserRepositoryDep,
    search: Annotated[str | None, Query(description="Busca en nombre, correo y teléfono")] = None,
    ordering: Annotated[str | None, Query(description="Columna, '-' invierte")] = None,
    is_active: Annotated[bool | None, Query(description="Filtra por estado")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ClientPageResponse:
    page = await ListUsers(users, CLIENT_ROLES)(
        UserQuery(
            search=search,
            is_active=is_active,
            ordering=ordering,
            limit=limit,
            offset=offset,
        )
    )
    return ClientPageResponse(
        items=[UserResponse.from_entity(user) for user in page.items],
        total=page.total,
    )


@router.post(
    "/walk-in",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Alta exprés de un cliente sin correo (emergencia)",
)
async def register_walk_in_client(
    payload: RegisterWalkInClientRequest,
    principal: WalkInRegistrarDep,
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    activity: ActivityRecorderDep,
) -> UserResponse:
    try:
        user = await RegisterWalkInClient(users, hasher, activity)(
            RegisterWalkInClientCommand(
                actor_id=principal.user_id,
                first_name=payload.first_name,
                last_name=payload.last_name,
                document_id=payload.document_id,
                phone=payload.phone,
            )
        )
    except (DocumentIdRequired, InvalidDocumentId) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return UserResponse.from_entity(user)


@router.post(
    "/document-lookup",
    response_model=DocumentLookupResponse,
    summary="Completar nombre y apellido desde el DNI (alta exprés)",
)
async def look_up_document(
    payload: DocumentLookupRequest,
    principal: WalkInRegistrarDep,
    identity: IdentityRegistryDep,
    activity: ActivityRecorderDep,
) -> DocumentLookupResponse:
    try:
        person = await LookUpDocument(identity, activity)(
            LookUpDocumentCommand(actor_id=principal.user_id, document_id=payload.document_id)
        )
    except (DocumentIdRequired, InvalidDocumentId) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except DocumentNotFoundInRegistry as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except IdentityRegistryUnavailable as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    return DocumentLookupResponse(first_names=person.first_names, last_names=person.last_names)


@router.patch(
    "/{client_id}/contact",
    response_model=UserResponse,
    summary="Completar el correo real de un cliente de alta exprés",
)
async def update_client_contact(
    client_id: int,
    payload: UpdateClientContactRequest,
    principal: ContactEditorDep,
    users: UserRepositoryDep,
    activity: ActivityRecorderDep,
) -> UserResponse:
    try:
        user = await UpdateClientContact(users, activity)(
            UpdateClientContactCommand(
                user_id=client_id,
                actor_id=principal.user_id,
                email=str(payload.email),
                phone=payload.phone,
                document_id=payload.document_id,
            )
        )
    except UserNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except EmailAlreadyRegistered as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except (InvalidEmail, InvalidDocumentId) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return UserResponse.from_entity(user)

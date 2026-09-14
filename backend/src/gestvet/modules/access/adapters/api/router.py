"""Adaptador de entrada HTTP para roles y permisos.

Todo el router exige administrar roles. Cada cambio avisa en tiempo real a las
cuentas afectadas, que vuelven a pedir sus permisos y la interfaz oculta o
muestra lo que corresponda sin cerrar sesión.
"""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Response, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import PrincipalDep, SessionDep, load_access, require_permission
from gestvet.core.permissions import Permission
from gestvet.core.realtime import PERMISSIONS_TOPIC, RealtimeEvent
from gestvet.core.realtime_broker import EventPublisherDep
from gestvet.modules.access.adapters.api.dependencies import (
    AccessRoleRepositoryDep,
    AccountDirectoryDep,
    RoleAssignmentsDep,
)
from gestvet.modules.access.adapters.api.schemas import (
    AccessRoleListResponse,
    AccessRoleResponse,
    AssignAccessRoleRequest,
    CreateAccessRoleRequest,
    PermissionCatalogResponse,
    RoleAssignmentListResponse,
    RoleAssignmentResponse,
    UpdateAccessRoleRequest,
)
from gestvet.modules.access.domain.entities import AccessRole
from gestvet.modules.access.domain.exceptions import (
    AccessError,
    AccessRoleLocked,
    AccessRoleNotFound,
    AccountNotFound,
    InvalidAccessRole,
    RoleInUse,
    RoleKindMismatch,
    RoleNameTaken,
)
from gestvet.modules.access.ports.repositories import RoleAssignments
from gestvet.modules.access.use_cases.manage_roles import (
    AssignAccessRole,
    AssignAccessRoleCommand,
    CreateAccessRole,
    CreateAccessRoleCommand,
    DeleteAccessRole,
    DeleteAccessRoleCommand,
    UpdateAccessRole,
    UpdateAccessRoleCommand,
)

router = APIRouter(dependencies=[Depends(require_permission(Permission.ROLES_MANAGE))])

_STATUS_BY_ERROR: tuple[tuple[type[AccessError], int], ...] = (
    (AccessRoleNotFound, status.HTTP_404_NOT_FOUND),
    (AccountNotFound, status.HTTP_404_NOT_FOUND),
    (RoleNameTaken, status.HTTP_409_CONFLICT),
    (RoleInUse, status.HTTP_409_CONFLICT),
    (AccessRoleLocked, status.HTTP_409_CONFLICT),
    (InvalidAccessRole, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (RoleKindMismatch, status.HTTP_422_UNPROCESSABLE_CONTENT),
)


def _to_http(error: AccessError) -> HTTPException:
    for error_type, code in _STATUS_BY_ERROR:
        if isinstance(error, error_type):
            return HTTPException(code, str(error))
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(error))


async def _notify_role_change(
    role: AccessRole, assignments: RoleAssignments, events: EventPublisherDep
) -> None:
    # Un rol de sistema lo usan todas las cuentas de su tipo sin rol asignado,
    # así que el aviso va al tipo entero; uno propio, solo a quien lo tiene.
    if role.is_system:
        event = RealtimeEvent(topic=PERMISSIONS_TOPIC, roles=frozenset({role.account_kind}))
    else:
        users = await assignments.users_with_role(role.id or 0)
        event = RealtimeEvent(topic=PERMISSIONS_TOPIC, user_ids=frozenset(users))
    events.publish(event)


@router.get("/permissions", response_model=PermissionCatalogResponse, summary="Catálogo")
async def list_permissions() -> PermissionCatalogResponse:
    return PermissionCatalogResponse.build()


@router.get("/roles", response_model=AccessRoleListResponse, summary="Roles y sus permisos")
async def list_roles(
    roles: AccessRoleRepositoryDep, assignments: RoleAssignmentsDep
) -> AccessRoleListResponse:
    counts = Counter((await assignments.all_assignments()).values())
    return AccessRoleListResponse(
        items=[
            AccessRoleResponse.from_entity(role, counts[role.id or 0])
            for role in await roles.list_all()
        ]
    )


@router.post(
    "/roles",
    response_model=AccessRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un rol",
)
async def create_role(
    payload: CreateAccessRoleRequest,
    principal: PrincipalDep,
    roles: AccessRoleRepositoryDep,
    activity: ActivityRecorderDep,
) -> AccessRoleResponse:
    try:
        role = await CreateAccessRole(roles, activity)(
            CreateAccessRoleCommand(
                actor_id=principal.user_id,
                name=payload.name,
                description=payload.description,
                account_kind=payload.account_kind,
                permissions=frozenset(payload.permissions),
            )
        )
    except AccessError as error:
        raise _to_http(error) from error
    return AccessRoleResponse.from_entity(role, 0)


@router.patch("/roles/{role_id}", response_model=AccessRoleResponse, summary="Editar un rol")
async def update_role(
    role_id: int,
    payload: UpdateAccessRoleRequest,
    principal: PrincipalDep,
    session: SessionDep,
    roles: AccessRoleRepositoryDep,
    assignments: RoleAssignmentsDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> AccessRoleResponse:
    propio = await load_access(session, principal.user_id)
    try:
        role = await UpdateAccessRole(roles, activity)(
            UpdateAccessRoleCommand(
                actor_id=principal.user_id,
                actor_role_id=propio.role_id,
                role_id=role_id,
                name=payload.name,
                description=payload.description,
                permissions=frozenset(payload.permissions),
            )
        )
    except AccessError as error:
        raise _to_http(error) from error
    await _notify_role_change(role, assignments, events)
    return AccessRoleResponse.from_entity(role, len(await assignments.users_with_role(role_id)))


@router.delete(
    "/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Borrar un rol sin uso"
)
async def delete_role(
    role_id: int,
    principal: PrincipalDep,
    roles: AccessRoleRepositoryDep,
    assignments: RoleAssignmentsDep,
    activity: ActivityRecorderDep,
) -> Response:
    try:
        await DeleteAccessRole(roles, assignments, activity)(
            DeleteAccessRoleCommand(actor_id=principal.user_id, role_id=role_id)
        )
    except AccessError as error:
        raise _to_http(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/assignments",
    response_model=RoleAssignmentListResponse,
    summary="Cuentas con un rol asignado",
)
async def list_assignments(assignments: RoleAssignmentsDep) -> RoleAssignmentListResponse:
    return RoleAssignmentListResponse(
        items=[
            RoleAssignmentResponse(user_id=user_id, role_id=role_id)
            for user_id, role_id in sorted((await assignments.all_assignments()).items())
        ]
    )


@router.put(
    "/users/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Asignar un rol a una cuenta",
)
async def assign_role(
    user_id: int,
    payload: AssignAccessRoleRequest,
    principal: PrincipalDep,
    roles: AccessRoleRepositoryDep,
    assignments: RoleAssignmentsDep,
    accounts: AccountDirectoryDep,
    activity: ActivityRecorderDep,
    events: EventPublisherDep,
) -> Response:
    try:
        await AssignAccessRole(roles, assignments, accounts, activity)(
            AssignAccessRoleCommand(
                actor_id=principal.user_id, user_id=user_id, role_id=payload.role_id
            )
        )
    except AccessError as error:
        raise _to_http(error) from error
    events.publish(RealtimeEvent(topic=PERMISSIONS_TOPIC, user_ids=frozenset({user_id})))
    return Response(status_code=status.HTTP_204_NO_CONTENT)

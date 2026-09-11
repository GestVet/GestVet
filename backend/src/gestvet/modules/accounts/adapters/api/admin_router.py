"""Adaptador de entrada HTTP para la administración de cuentas.

Alta de veterinarios, listado del personal, activación y turno de guardia.
Todo el router exige rol de administración: la comprobación va una sola vez en
su declaración, en lugar de repetirse en cada endpoint.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity import ActivityKind
from gestvet.core.activity_log import ActivityReaderDep, ActivityRecorderDep
from gestvet.core.auth import PrincipalDep, require_roles
from gestvet.core.identity import Role
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.modules.accounts.adapters.api.dependencies import (
    PasswordHasherDep,
    UserRepositoryDep,
)
from gestvet.modules.accounts.adapters.api.schemas import (
    ActivityPageResponse,
    ActivityResponse,
    ChangeUserStatusRequest,
    ClientPageResponse,
    RegisterStaffRequest,
    UserResponse,
)
from gestvet.modules.accounts.domain.exceptions import (
    CannotDeactivateSelf,
    EmailAlreadyRegistered,
    InvalidEmail,
    RoleNotAssignable,
    RoleNotSwappable,
    UserNotFound,
)
from gestvet.modules.accounts.ports.user_repository import UserQuery
from gestvet.modules.accounts.use_cases.list_clients import STAFF_LISTING_ROLES, ListUsers
from gestvet.modules.accounts.use_cases.manage_accounts import (
    ChangeUserStatus,
    ChangeUserStatusCommand,
    RegisterStaff,
    RegisterStaffCommand,
    ToggleGuardDuty,
    ToggleGuardDutyCommand,
)
from gestvet.modules.accounts.use_cases.read_activity import ReadActivity, ReadActivityQuery

router = APIRouter(dependencies=[Depends(require_roles(Role.ADMIN))])


@router.post(
    "/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un veterinario",
)
async def register_staff(
    payload: RegisterStaffRequest,
    principal: PrincipalDep,
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    activity: ActivityRecorderDep,
) -> UserResponse:
    try:
        user = await RegisterStaff(users, hasher, activity)(
            RegisterStaffCommand(
                actor_id=principal.user_id,
                email=str(payload.email),
                password=payload.password,
                first_name=payload.first_name,
                last_name=payload.last_name,
                role=payload.role,
                phone=payload.phone,
            )
        )
    except EmailAlreadyRegistered as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except (InvalidEmail, RoleNotAssignable) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return UserResponse.from_entity(user)


@router.get("/staff", response_model=ClientPageResponse, summary="Listar el personal")
async def list_staff(
    users: UserRepositoryDep,
    search: Annotated[str | None, Query(description="Busca en nombre, correo y teléfono")] = None,
    is_active: Annotated[bool | None, Query(description="Filtra por estado")] = None,
    ordering: Annotated[str | None, Query(description="Columna, '-' invierte")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ClientPageResponse:
    page = await ListUsers(users, STAFF_LISTING_ROLES)(
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


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="Activar o desactivar una cuenta",
)
async def change_user_status(
    user_id: int,
    payload: ChangeUserStatusRequest,
    principal: PrincipalDep,
    users: UserRepositoryDep,
    activity: ActivityRecorderDep,
) -> UserResponse:
    try:
        user = await ChangeUserStatus(users, activity)(
            ChangeUserStatusCommand(
                user_id=user_id,
                actor_id=principal.user_id,
                is_active=payload.is_active,
            )
        )
    except UserNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except CannotDeactivateSelf as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return UserResponse.from_entity(user)


@router.post(
    "/staff/{user_id}/guard-duty",
    response_model=UserResponse,
    summary="Poner o sacar del turno de guardia",
)
async def toggle_guard_duty(
    user_id: int,
    principal: PrincipalDep,
    users: UserRepositoryDep,
    activity: ActivityRecorderDep,
) -> UserResponse:
    try:
        user = await ToggleGuardDuty(users, activity)(
            ToggleGuardDutyCommand(user_id=user_id, actor_id=principal.user_id)
        )
    except UserNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except RoleNotSwappable as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return UserResponse.from_entity(user)


@router.get(
    "/activity",
    response_model=ActivityPageResponse,
    summary="Movimientos de las cuentas",
)
async def read_activity(
    activity: ActivityReaderDep,
    users: UserRepositoryDep,
    role: Annotated[list[Role] | None, Query(description="Filtra por rol")] = None,
    kind: Annotated[list[ActivityKind] | None, Query(description="Filtra por acción")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ActivityPageResponse:
    # El original escondia las acciones del administrador con un `id_rol != 1`
    # fijo en la consulta. Una bitacora que oculta al actor mas poderoso no
    # sirve para auditar, asi que aca el rol es un filtro y no una exclusion.
    page = await ReadActivity(activity, users)(
        ReadActivityQuery(
            roles=frozenset(role) if role else None,
            kinds=frozenset(kind) if kind else None,
            limit=limit,
            offset=offset,
        )
    )
    return ActivityPageResponse(
        items=[
            ActivityResponse(
                id=entrada.record.id or 0,
                kind=entrada.record.kind.value,
                kind_label=entrada.record.kind.label,
                detail=entrada.record.detail,
                occurred_at=entrada.record.occurred_at,
                user_id=entrada.user.id or 0,
                user_name=entrada.user.full_name,
                user_role=entrada.user.role,
            )
            for entrada in page.items
        ],
        total=page.total,
    )

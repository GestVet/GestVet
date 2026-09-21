"""Adaptador de entrada HTTP para la administración de cuentas.

Alta de veterinarios, listado del personal y activación.
Cada endpoint exige su permiso; los roles de sistema se los dan a la
administración.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity import ActivityKind
from gestvet.core.activity_log import ActivityReaderDep, ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal, Role
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.core.permissions import Permission
from gestvet.modules.accounts.adapters.api.dependencies import (
    PasswordHasherDep,
    SpecialtyRepositoryDep,
    UserRepositoryDep,
)
from gestvet.modules.accounts.adapters.api.schemas import (
    ActivityPageResponse,
    ActivityResponse,
    AssignVeterinarianSpecialtiesRequest,
    ChangeUserStatusRequest,
    ClientPageResponse,
    RegisterStaffRequest,
    SpecialtyResponse,
    UserResponse,
    VeterinarianSpecialtiesListResponse,
    VeterinarianSpecialtiesResponse,
)
from gestvet.modules.accounts.domain.exceptions import (
    CannotDeactivateSelf,
    EmailAlreadyRegistered,
    InvalidEmail,
    RoleNotAssignable,
    SpecialtiesRequired,
    UnknownSpecialties,
    UserNotFound,
)
from gestvet.modules.accounts.ports.user_repository import UserQuery
from gestvet.modules.accounts.use_cases.list_clients import (
    BOOKABLE_VETERINARIAN_ROLES,
    STAFF_LISTING_ROLES,
    ListUsers,
)
from gestvet.modules.accounts.use_cases.manage_accounts import (
    ChangeUserStatus,
    ChangeUserStatusCommand,
    RegisterStaff,
    RegisterStaffCommand,
)
from gestvet.modules.accounts.use_cases.manage_specialties import (
    AssignVeterinarianSpecialties,
    AssignVeterinarianSpecialtiesCommand,
)
from gestvet.modules.accounts.use_cases.read_activity import ReadActivity, ReadActivityQuery

router = APIRouter()

StaffManagerDep = Annotated[Principal, Depends(require_permission(Permission.STAFF_MANAGE))]
StatusManagerDep = Annotated[Principal, Depends(require_permission(Permission.USERS_CHANGE_STATUS))]


@router.post(
    "/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un veterinario",
)
async def register_staff(
    payload: RegisterStaffRequest,
    principal: StaffManagerDep,
    users: UserRepositoryDep,
    specialties: SpecialtyRepositoryDep,
    hasher: PasswordHasherDep,
    activity: ActivityRecorderDep,
) -> UserResponse:
    try:
        user = await RegisterStaff(users, specialties, hasher, activity)(
            RegisterStaffCommand(
                actor_id=principal.user_id,
                email=str(payload.email),
                password=payload.password,
                first_name=payload.first_name,
                last_name=payload.last_name,
                role=payload.role,
                specialty_ids=frozenset(payload.specialty_ids),
                phone=payload.phone,
            )
        )
    except EmailAlreadyRegistered as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except (InvalidEmail, RoleNotAssignable, SpecialtiesRequired, UnknownSpecialties) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return UserResponse.from_entity(user)


@router.get(
    "/staff/specialties",
    response_model=VeterinarianSpecialtiesListResponse,
    dependencies=[Depends(require_permission(Permission.STAFF_READ))],
    summary="Especialidades asignadas a cada veterinario",
)
async def list_staff_specialties(
    users: UserRepositoryDep, specialties: SpecialtyRepositoryDep
) -> VeterinarianSpecialtiesListResponse:
    page = await ListUsers(users, BOOKABLE_VETERINARIAN_ROLES)(UserQuery(limit=MAX_PAGE_SIZE))
    by_user = await specialties.specialties_for(
        frozenset(user.id for user in page.items if user.id is not None)
    )
    return VeterinarianSpecialtiesListResponse(
        items=[
            VeterinarianSpecialtiesResponse(
                user_id=user.id or 0,
                specialties=[
                    SpecialtyResponse.from_entity(specialty)
                    for specialty in by_user.get(user.id or 0, [])
                ],
            )
            for user in page.items
        ]
    )


@router.put(
    "/staff/{user_id}/specialties",
    response_model=VeterinarianSpecialtiesResponse,
    summary="Asignar las especialidades de un veterinario",
)
async def assign_veterinarian_specialties(
    user_id: int,
    payload: AssignVeterinarianSpecialtiesRequest,
    principal: StaffManagerDep,
    users: UserRepositoryDep,
    specialties: SpecialtyRepositoryDep,
    activity: ActivityRecorderDep,
) -> VeterinarianSpecialtiesResponse:
    try:
        resultado = await AssignVeterinarianSpecialties(users, specialties, activity)(
            AssignVeterinarianSpecialtiesCommand(
                actor_id=principal.user_id,
                veterinarian_id=user_id,
                specialty_ids=frozenset(payload.specialty_ids),
            )
        )
    except UserNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except (SpecialtiesRequired, UnknownSpecialties) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return VeterinarianSpecialtiesResponse(
        user_id=user_id,
        specialties=[SpecialtyResponse.from_entity(specialty) for specialty in resultado],
    )


@router.get(
    "/staff",
    response_model=ClientPageResponse,
    dependencies=[Depends(require_permission(Permission.STAFF_READ))],
    summary="Listar el personal",
)
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
    principal: StatusManagerDep,
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


@router.get(
    "/activity",
    response_model=ActivityPageResponse,
    dependencies=[Depends(require_permission(Permission.ACTIVITY_READ))],
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

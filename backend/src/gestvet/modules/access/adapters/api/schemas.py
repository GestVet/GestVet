"""Contrato HTTP del módulo de accesos."""

from __future__ import annotations

from pydantic import BaseModel, Field

from gestvet.core.identity import Role
from gestvet.core.permissions import CATALOG, PERMISSION_GROUPS, Permission
from gestvet.modules.access.domain.entities import (
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    MIN_NAME_LENGTH,
    AccessRole,
)


class PermissionResponse(BaseModel):
    code: Permission
    label: str
    group: str
    account_kinds: list[Role]


class PermissionCatalogResponse(BaseModel):
    groups: list[str]
    items: list[PermissionResponse]

    @classmethod
    def build(cls) -> PermissionCatalogResponse:
        return cls(
            groups=list(PERMISSION_GROUPS),
            items=[
                PermissionResponse(
                    code=code,
                    label=info.label,
                    group=info.group,
                    account_kinds=sorted(info.account_kinds),
                )
                for code, info in CATALOG.items()
            ],
        )


class AccessRoleResponse(BaseModel):
    id: int
    name: str
    description: str
    account_kind: Role
    is_system: bool
    permissions: list[Permission]
    # Cuentas con este rol asignado. Un rol de sistema también lo usan todas
    # las cuentas de su tipo sin rol asignado, que no se cuentan acá.
    assigned_count: int

    @classmethod
    def from_entity(cls, role: AccessRole, assigned_count: int) -> AccessRoleResponse:
        return cls(
            id=role.id or 0,
            name=role.name,
            description=role.description,
            account_kind=role.account_kind,
            is_system=role.is_system,
            permissions=sorted(role.permissions),
            assigned_count=assigned_count,
        )


class AccessRoleListResponse(BaseModel):
    items: list[AccessRoleResponse]


class UpdateAccessRoleRequest(BaseModel):
    name: str = Field(min_length=MIN_NAME_LENGTH, max_length=MAX_NAME_LENGTH)
    description: str = Field(default="", max_length=MAX_DESCRIPTION_LENGTH)
    permissions: list[Permission]


class CreateAccessRoleRequest(UpdateAccessRoleRequest):
    account_kind: Role


class AssignAccessRoleRequest(BaseModel):
    """Sin `role_id`, la cuenta vuelve al rol de sistema de su tipo."""

    role_id: int | None = Field(default=None, ge=1)


class RoleAssignmentResponse(BaseModel):
    user_id: int
    role_id: int


class RoleAssignmentListResponse(BaseModel):
    items: list[RoleAssignmentResponse]

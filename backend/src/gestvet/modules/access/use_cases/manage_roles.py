"""Casos de uso: crear, editar, borrar y asignar roles.

Tres reglas cuidan que la clínica no se quede sin forma de administrar roles:
el rol de sistema de administración conserva ese permiso, nadie se lo quita a
su propio rol y nadie se cambia su propio rol.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity import Role
from gestvet.core.permissions import Permission
from gestvet.modules.access.domain.entities import AccessRole, parse_permissions
from gestvet.modules.access.domain.exceptions import (
    AccessRoleLocked,
    AccessRoleNotFound,
    AccountNotFound,
    RoleInUse,
    RoleKindMismatch,
    RoleNameTaken,
)
from gestvet.modules.access.ports.repositories import (
    AccessRoleRepository,
    AccountDirectory,
    RoleAssignments,
)


async def _require_role(roles: AccessRoleRepository, role_id: int) -> AccessRole:
    role = await roles.get(role_id)
    if role is None:
        raise AccessRoleNotFound(role_id)
    return role


async def _ensure_name_free(roles: AccessRoleRepository, name: str, own_id: int | None) -> None:
    existente = await roles.get_by_name(name)
    if existente is not None and existente.id != own_id:
        raise RoleNameTaken(name)


@dataclass(frozen=True, slots=True)
class CreateAccessRoleCommand:
    actor_id: int
    name: str
    account_kind: Role
    permissions: frozenset[str]
    description: str = ""


class CreateAccessRole:
    def __init__(self, roles: AccessRoleRepository, activity: ActivityRecorder) -> None:
        self._roles = roles
        self._activity = activity

    async def __call__(self, command: CreateAccessRoleCommand) -> AccessRole:
        role = AccessRole(
            name=command.name,
            account_kind=command.account_kind,
            permissions=parse_permissions(command.permissions),
            description=command.description,
        )
        await _ensure_name_free(self._roles, role.name, None)
        creado = await self._roles.add(role)
        await self._activity.record(command.actor_id, ActivityKind.ACCESS_ROLE_CREATED, creado.name)
        return creado


@dataclass(frozen=True, slots=True)
class UpdateAccessRoleCommand:
    actor_id: int
    actor_role_id: int | None
    role_id: int
    name: str
    permissions: frozenset[str]
    description: str = ""


class UpdateAccessRole:
    def __init__(self, roles: AccessRoleRepository, activity: ActivityRecorder) -> None:
        self._roles = roles
        self._activity = activity

    async def __call__(self, command: UpdateAccessRoleCommand) -> AccessRole:
        actual = await _require_role(self._roles, command.role_id)
        nuevo = replace(
            actual,
            name=command.name,
            description=command.description,
            permissions=parse_permissions(command.permissions),
        )
        if actual.is_system and nuevo.name != actual.name:
            # El nombre del rol de sistema es el que ve una cuenta sin rol
            # asignado: cambiarlo haría creer que es un rol distinto.
            raise AccessRoleLocked("El nombre de un rol de sistema no se cambia.")
        if command.actor_role_id == actual.id and Permission.ROLES_MANAGE not in nuevo.permissions:
            raise AccessRoleLocked(
                "No puedes quitarle a tu propio rol el permiso de administrar roles."
            )
        await _ensure_name_free(self._roles, nuevo.name, actual.id)
        guardado = await self._roles.save(nuevo)
        await self._activity.record(
            command.actor_id, ActivityKind.ACCESS_ROLE_UPDATED, guardado.name
        )
        return guardado


@dataclass(frozen=True, slots=True)
class DeleteAccessRoleCommand:
    actor_id: int
    role_id: int


class DeleteAccessRole:
    def __init__(
        self,
        roles: AccessRoleRepository,
        assignments: RoleAssignments,
        activity: ActivityRecorder,
    ) -> None:
        self._roles = roles
        self._assignments = assignments
        self._activity = activity

    async def __call__(self, command: DeleteAccessRoleCommand) -> None:
        actual = await _require_role(self._roles, command.role_id)
        if actual.is_system:
            raise AccessRoleLocked("Los roles de sistema no se borran.")
        asignadas = await self._assignments.users_with_role(command.role_id)
        if asignadas:
            raise RoleInUse(len(asignadas))
        await self._roles.delete(command.role_id)
        await self._activity.record(command.actor_id, ActivityKind.ACCESS_ROLE_DELETED, actual.name)


@dataclass(frozen=True, slots=True)
class AssignAccessRoleCommand:
    actor_id: int
    user_id: int
    role_id: int | None


class AssignAccessRole:
    """Asigna un rol a una cuenta, o la devuelve al rol de sistema de su tipo."""

    def __init__(
        self,
        roles: AccessRoleRepository,
        assignments: RoleAssignments,
        accounts: AccountDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._roles = roles
        self._assignments = assignments
        self._accounts = accounts
        self._activity = activity

    async def __call__(self, command: AssignAccessRoleCommand) -> AccessRole | None:
        if command.user_id == command.actor_id:
            raise AccessRoleLocked("No puedes cambiar tu propio rol.")
        cuenta = await self._accounts.get(command.user_id)
        if cuenta is None:
            raise AccountNotFound(command.user_id)

        role = await self._effective_role(command.role_id, cuenta.account_kind)
        if role is None or role.is_system:
            # El rol de sistema no se guarda como asignación: es lo que ya tiene
            # toda cuenta sin rol, y así sigue a su tipo si este cambia.
            await self._assignments.clear(command.user_id)
        else:
            await self._assignments.assign(command.user_id, role.id or 0)

        nombre = role.name if role is not None else "rol de sistema"
        await self._activity.record(
            command.actor_id,
            ActivityKind.ACCESS_ROLE_ASSIGNED,
            f"cuenta {command.user_id}: {nombre}",
        )
        return role

    async def _effective_role(self, role_id: int | None, account_kind: Role) -> AccessRole | None:
        if role_id is None:
            return await self._roles.get_system(account_kind)
        role = await _require_role(self._roles, role_id)
        if role.account_kind is not account_kind:
            raise RoleKindMismatch(role.account_kind.value, account_kind.value)
        return role

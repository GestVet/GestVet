from __future__ import annotations

from collections import defaultdict

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.identity import Role
from gestvet.core.permissions import Permission
from gestvet.modules.access.adapters.persistence.models import (
    AccessRolePermissionRow,
    AccessRoleRow,
    UserAccessRoleRow,
)
from gestvet.modules.access.domain.entities import AccessRole
from gestvet.modules.access.ports.repositories import AccountSummary

_KNOWN = frozenset(Permission.__members__.values())

# Lectura de la tabla de `accounts`: solo el tipo de cuenta, nunca se escribe.
_ACCOUNT_KIND = text("SELECT id, role FROM users WHERE id = :user_id")


def _to_entity(row: AccessRoleRow, codes: set[str]) -> AccessRole:
    # Un código que el catálogo ya no conoce se ignora en vez de romper la
    # lectura: el permiso dejó de existir y ningún endpoint lo exige.
    return AccessRole(
        id=row.id,
        name=row.name,
        description=row.description,
        account_kind=Role(row.account_kind),
        is_system=row.is_system,
        permissions=frozenset(Permission(code) for code in codes if code in _KNOWN),
        created_at=row.created_at,
    )


class SqlAlchemyAccessRoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[AccessRole]:
        rows = (
            await self._session.execute(
                select(AccessRoleRow).order_by(AccessRoleRow.is_system.desc(), AccessRoleRow.name)
            )
        ).scalars()
        roles = list(rows)
        codes = await self._codes_by_role([row.id for row in roles])
        return [_to_entity(row, codes[row.id]) for row in roles]

    async def get(self, role_id: int) -> AccessRole | None:
        row = await self._session.get(AccessRoleRow, role_id)
        return await self._with_codes(row)

    async def get_by_name(self, name: str) -> AccessRole | None:
        row = (
            await self._session.execute(
                select(AccessRoleRow).where(func.lower(AccessRoleRow.name) == name.lower())
            )
        ).scalar_one_or_none()
        return await self._with_codes(row)

    async def get_system(self, account_kind: Role) -> AccessRole | None:
        row = (
            await self._session.execute(
                select(AccessRoleRow).where(
                    AccessRoleRow.is_system.is_(True),
                    AccessRoleRow.account_kind == account_kind.value,
                )
            )
        ).scalar_one_or_none()
        return await self._with_codes(row)

    async def add(self, role: AccessRole) -> AccessRole:
        row = AccessRoleRow(
            name=role.name,
            description=role.description,
            account_kind=role.account_kind.value,
            is_system=role.is_system,
            created_at=role.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._replace_permissions(row.id, role.permissions)
        return _to_entity(row, {permission.value for permission in role.permissions})

    async def save(self, role: AccessRole) -> AccessRole:
        row = await self._session.get(AccessRoleRow, role.id)
        if row is None:
            raise LookupError(role.id)
        row.name = role.name
        row.description = role.description
        await self._session.flush()
        await self._replace_permissions(row.id, role.permissions)
        return _to_entity(row, {permission.value for permission in role.permissions})

    async def delete(self, role_id: int) -> None:
        await self._session.execute(
            delete(AccessRolePermissionRow).where(AccessRolePermissionRow.role_id == role_id)
        )
        await self._session.execute(delete(AccessRoleRow).where(AccessRoleRow.id == role_id))
        await self._session.flush()

    async def _with_codes(self, row: AccessRoleRow | None) -> AccessRole | None:
        if row is None:
            return None
        codes = await self._codes_by_role([row.id])
        return _to_entity(row, codes[row.id])

    async def _codes_by_role(self, role_ids: list[int]) -> defaultdict[int, set[str]]:
        codes: defaultdict[int, set[str]] = defaultdict(set)
        if not role_ids:
            return codes
        rows = await self._session.execute(
            select(AccessRolePermissionRow).where(AccessRolePermissionRow.role_id.in_(role_ids))
        )
        for row in rows.scalars():
            codes[row.role_id].add(row.permission)
        return codes

    async def _replace_permissions(self, role_id: int, permissions: frozenset[Permission]) -> None:
        await self._session.execute(
            delete(AccessRolePermissionRow).where(AccessRolePermissionRow.role_id == role_id)
        )
        self._session.add_all(
            AccessRolePermissionRow(role_id=role_id, permission=permission.value)
            for permission in sorted(permissions)
        )
        await self._session.flush()


class SqlRoleAssignments:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def role_of(self, user_id: int) -> int | None:
        row = await self._session.get(UserAccessRoleRow, user_id)
        return row.role_id if row is not None else None

    async def assign(self, user_id: int, role_id: int) -> None:
        row = await self._session.get(UserAccessRoleRow, user_id)
        if row is None:
            self._session.add(UserAccessRoleRow(user_id=user_id, role_id=role_id))
        else:
            row.role_id = role_id
        await self._session.flush()

    async def clear(self, user_id: int) -> None:
        await self._session.execute(
            delete(UserAccessRoleRow).where(UserAccessRoleRow.user_id == user_id)
        )
        await self._session.flush()

    async def users_with_role(self, role_id: int) -> list[int]:
        rows = await self._session.execute(
            select(UserAccessRoleRow.user_id).where(UserAccessRoleRow.role_id == role_id)
        )
        return [int(user_id) for user_id in rows.scalars()]

    async def all_assignments(self) -> dict[int, int]:
        rows = await self._session.execute(select(UserAccessRoleRow))
        return {row.user_id: row.role_id for row in rows.scalars()}


class SqlAccountDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> AccountSummary | None:
        row = (await self._session.execute(_ACCOUNT_KIND, {"user_id": user_id})).first()
        if row is None:
            return None
        return AccountSummary(user_id=int(row.id), account_kind=Role(row.role))

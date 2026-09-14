from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.access.adapters.persistence.repositories import (
    SqlAccountDirectory,
    SqlAlchemyAccessRoleRepository,
    SqlRoleAssignments,
)
from gestvet.modules.access.ports.repositories import (
    AccessRoleRepository,
    AccountDirectory,
    RoleAssignments,
)


def get_access_role_repository(session: SessionDep) -> AccessRoleRepository:
    return SqlAlchemyAccessRoleRepository(session)


def get_role_assignments(session: SessionDep) -> RoleAssignments:
    return SqlRoleAssignments(session)


def get_account_directory(session: SessionDep) -> AccountDirectory:
    return SqlAccountDirectory(session)


AccessRoleRepositoryDep = Annotated[AccessRoleRepository, Depends(get_access_role_repository)]
RoleAssignmentsDep = Annotated[RoleAssignments, Depends(get_role_assignments)]
AccountDirectoryDep = Annotated[AccountDirectory, Depends(get_account_directory)]

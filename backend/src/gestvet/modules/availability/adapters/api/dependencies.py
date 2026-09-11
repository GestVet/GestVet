from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.availability.adapters.persistence.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityRepository,
)
from gestvet.modules.availability.ports.availability_repository import AvailabilityRepository


def get_availability_repository(session: SessionDep) -> AvailabilityRepository:
    return SqlAlchemyAvailabilityRepository(session)


AvailabilityRepositoryDep = Annotated[AvailabilityRepository, Depends(get_availability_repository)]

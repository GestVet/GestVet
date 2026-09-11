"""Cableado del adaptador HTTP de disponibilidad."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.availability.adapters.persistence.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityRepository,
)
from gestvet.availability.ports.availability_repository import AvailabilityRepository
from gestvet.core.auth import SessionDep


def get_availability_repository(session: SessionDep) -> AvailabilityRepository:
    return SqlAlchemyAvailabilityRepository(session)


AvailabilityRepositoryDep = Annotated[AvailabilityRepository, Depends(get_availability_repository)]

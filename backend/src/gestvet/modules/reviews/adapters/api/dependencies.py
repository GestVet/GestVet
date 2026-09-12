from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.modules.reviews.adapters.persistence.directories import SqlAppointmentDirectory
from gestvet.modules.reviews.adapters.persistence.repositories import SqlAlchemyReviewRepository
from gestvet.modules.reviews.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.reviews.ports.review_repository import ReviewRepository


def get_review_repository(session: SessionDep) -> ReviewRepository:
    return SqlAlchemyReviewRepository(session)


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


ReviewRepositoryDep = Annotated[ReviewRepository, Depends(get_review_repository)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]

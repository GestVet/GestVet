"""Adaptador de entrada HTTP para reseñas.

Solo un cliente deja reseña, y solo del veterinario que de verdad lo atendió.
Leerlas es público entre cuentas autenticadas: un cliente las mira para
elegir veterinario al reservar, y administración para ver cómo viene la
atención de cada uno.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import require_permission
from gestvet.core.identity import Principal
from gestvet.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from gestvet.core.permissions import Permission
from gestvet.modules.reviews.adapters.api.dependencies import (
    AppointmentDirectoryDep,
    ReviewRepositoryDep,
)
from gestvet.modules.reviews.adapters.api.schemas import (
    ReviewResponse,
    SubmitReviewRequest,
    VeterinarianReviewsResponse,
)
from gestvet.modules.reviews.domain.exceptions import (
    InappropriateComment,
    InvalidReview,
    NotEligibleToReview,
)
from gestvet.modules.reviews.ports.review_repository import ReviewQuery
from gestvet.modules.reviews.use_cases.list_veterinarian_reviews import ListVeterinarianReviews
from gestvet.modules.reviews.use_cases.submit_review import SubmitReview, SubmitReviewCommand

router = APIRouter()

ReviewerDep = Annotated[Principal, Depends(require_permission(Permission.REVIEWS_SUBMIT))]
ReviewsReaderDep = Annotated[Principal, Depends(require_permission(Permission.REVIEWS_READ))]


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dejar o actualizar una reseña de un veterinario",
)
async def submit_review(
    payload: SubmitReviewRequest,
    client: ReviewerDep,
    reviews: ReviewRepositoryDep,
    appointments: AppointmentDirectoryDep,
    activity: ActivityRecorderDep,
) -> ReviewResponse:
    try:
        review = await SubmitReview(reviews, appointments, activity)(
            SubmitReviewCommand(
                veterinarian_id=payload.veterinarian_id,
                client_id=client.user_id,
                rating=payload.rating,
                comment=payload.comment,
            )
        )
    except NotEligibleToReview as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    except (InvalidReview, InappropriateComment) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return ReviewResponse.from_entity(review)


@router.get(
    "",
    response_model=VeterinarianReviewsResponse,
    summary="Reseñas y promedio de un veterinario",
)
async def list_veterinarian_reviews(
    _principal: ReviewsReaderDep,
    reviews: ReviewRepositoryDep,
    veterinarian_id: Annotated[int, Query(ge=1)],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> VeterinarianReviewsResponse:
    result = await ListVeterinarianReviews(reviews)(
        ReviewQuery(veterinarian_id=veterinarian_id, limit=limit, offset=offset)
    )
    return VeterinarianReviewsResponse.from_result(result)

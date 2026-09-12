"""Caso de uso: dejar o actualizar una reseña de un veterinario.

Volver a llamarlo con el mismo cliente y veterinario actualiza la reseña
existente: una persona no acumula varias calificaciones sobre el mismo
veterinario, cambia de opinión sobre la que ya dejó.
"""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.modules.reviews.domain.entities import Review
from gestvet.modules.reviews.domain.exceptions import NotEligibleToReview
from gestvet.modules.reviews.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.reviews.ports.review_repository import ReviewRepository


@dataclass(frozen=True, slots=True)
class SubmitReviewCommand:
    veterinarian_id: int
    client_id: int
    rating: int
    comment: str


class SubmitReview:
    def __init__(
        self,
        reviews: ReviewRepository,
        appointments: AppointmentDirectory,
        activity: ActivityRecorder,
    ) -> None:
        self._reviews = reviews
        self._appointments = appointments
        self._activity = activity

    async def __call__(self, command: SubmitReviewCommand) -> Review:
        elegible = await self._appointments.has_completed_appointment(
            command.client_id, command.veterinarian_id
        )
        if not elegible:
            raise NotEligibleToReview(command.veterinarian_id)

        existente = await self._reviews.find_by_client_and_veterinarian(
            command.client_id, command.veterinarian_id
        )
        if existente is not None:
            existente.update(rating=command.rating, comment=command.comment)
            guardada = await self._reviews.save(existente)
        else:
            nueva = Review(
                veterinarian_id=command.veterinarian_id,
                client_id=command.client_id,
                rating=command.rating,
                comment=command.comment,
            )
            guardada = await self._reviews.add(nueva)

        await self._activity.record(
            command.client_id,
            ActivityKind.REVIEW_SUBMITTED,
            f"{guardada.rating}★ al veterinario {guardada.veterinarian_id}",
        )
        return guardada

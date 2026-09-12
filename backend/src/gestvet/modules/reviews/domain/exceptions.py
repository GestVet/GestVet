"""Errores de dominio de reseñas.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class ReviewsError(Exception):
    """Raíz de los errores del módulo de reseñas."""


class InvalidReview(ReviewsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class InappropriateComment(ReviewsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class NotEligibleToReview(ReviewsError):
    """Solo reseña a un veterinario quien tuvo al menos una cita completada con él."""

    def __init__(self, veterinarian_id: int) -> None:
        super().__init__(
            f"Solo podés reseñar al veterinario {veterinarian_id} si tuviste una cita "
            "completada con él."
        )
        self.veterinarian_id = veterinarian_id

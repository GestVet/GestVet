"""Entidades de dominio de reseñas.

Python puro. El veterinario y el cliente se referencian por identificador:
cada uno vive en otro módulo y este no puede importarlos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from gestvet.modules.reviews.domain.exceptions import InappropriateComment, InvalidReview

MIN_RATING = 1
MAX_RATING = 5
MAX_COMMENT_LENGTH = 500

# Lista acotada a propósito: alcanza para frenar el insulto directo, no para
# un filtro de moderación completo. Una reseña que la esquive todavía puede
# rechazarse a mano desde la bitácora de actividad.
_BANNED_WORDS = frozenset(
    {
        "mierda",
        "puta",
        "puto",
        "putas",
        "putos",
        "pendejo",
        "pendeja",
        "imbecil",
        "imbécil",
        "estupido",
        "estúpido",
        "estupida",
        "estúpida",
        "idiota",
        "maldito",
        "maldita",
        "carajo",
        "cabron",
        "cabrón",
        "verga",
        "chinga",
        "coño",
        "joder",
        "gilipollas",
    }
)


@dataclass(slots=True)
class Review:
    """La calificación de un cliente sobre un veterinario.

    Una por cliente y veterinario: volver a calificar actualiza la reseña
    existente en vez de acumular otra, para que el promedio no se infle con
    reseñas repetidas de la misma persona.
    """

    veterinarian_id: int
    client_id: int
    rating: int
    comment: str
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.comment = _validate(self.rating, self.comment)

    def update(self, *, rating: int, comment: str, now: datetime | None = None) -> None:
        self.comment = _validate(rating, comment)
        self.rating = rating
        self.updated_at = now or datetime.now(UTC)


def _validate(rating: int, comment: str) -> str:
    if not MIN_RATING <= rating <= MAX_RATING:
        raise InvalidReview(f"La calificación debe ser de {MIN_RATING} a {MAX_RATING} estrellas.")
    cleaned = comment.strip()
    if not cleaned:
        raise InvalidReview("El comentario es obligatorio.")
    if len(cleaned) > MAX_COMMENT_LENGTH:
        raise InvalidReview(f"El comentario admite {MAX_COMMENT_LENGTH} caracteres como máximo.")
    _require_no_profanity(cleaned)
    return cleaned


def _require_no_profanity(comment: str) -> None:
    words = re.findall(r"\w+", comment.lower())
    if any(word in _BANNED_WORDS for word in words):
        raise InappropriateComment("El comentario incluye lenguaje que no se admite. Reformulalo.")

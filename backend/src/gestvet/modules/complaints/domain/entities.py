"""Entidades de dominio de reclamos.

Python puro. El cliente, el veterinario y la cita se referencian por
identificador: cada uno vive en otro módulo y este no puede importarlos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from gestvet.modules.complaints.domain.exceptions import InvalidComplaint

MAX_DESCRIPTION_LENGTH = 2000


@dataclass(slots=True)
class Complaint:
    """Un reclamo de un cliente sobre la atención de una cita puntual.

    El veterinario no lo elige quien reclama: se toma de la propia cita, para
    que nadie pueda reclamarle a alguien que nunca lo atendió.
    """

    client_id: int
    veterinarian_id: int
    appointment_id: int
    description: str
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        cleaned = self.description.strip()
        if not cleaned:
            raise InvalidComplaint("La descripción del reclamo es obligatoria.")
        if len(cleaned) > MAX_DESCRIPTION_LENGTH:
            raise InvalidComplaint(
                f"La descripción admite {MAX_DESCRIPTION_LENGTH} caracteres como máximo."
            )
        self.description = cleaned

"""Entidades de dominio de internaciones.

Python puro. La mascota, el veterinario y la cita se referencian por
identificador: cada uno vive en otro módulo y este no puede importarlos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from gestvet.modules.hospitalizations.domain.exceptions import (
    HospitalizationAlreadyDischarged,
    InvalidHospitalization,
)

MAX_REASON_LENGTH = 300
MAX_NOTE_LENGTH = 1000
MAX_DISCHARGE_NOTES_LENGTH = 1000


class HospitalizationStatus(StrEnum):
    OPEN = "open"
    DISCHARGED = "discharged"

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]


_STATUS_LABELS: dict[HospitalizationStatus, str] = {
    HospitalizationStatus.OPEN: "Internada",
    HospitalizationStatus.DISCHARGED: "Dada de alta",
}


@dataclass(slots=True)
class Hospitalization:
    """Una mascota que queda al cuidado de la clínica tras una cita puntual.

    Nace de una cita -cirugía, esterilización compleja, emergencia- porque es
    la atención que la motiva; a criterio del veterinario, no del dueño.
    """

    appointment_id: int
    pet_id: int
    opened_by: int
    reason: str
    status: HospitalizationStatus = HospitalizationStatus.OPEN
    discharge_notes: str = ""
    id: int | None = None
    admitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    discharged_at: datetime | None = None

    def __post_init__(self) -> None:
        self.reason = _require_text(self.reason, "motivo", MAX_REASON_LENGTH)
        self.discharge_notes = _trim(
            self.discharge_notes, "notas de alta", MAX_DISCHARGE_NOTES_LENGTH
        )

    @property
    def is_open(self) -> bool:
        return self.status is HospitalizationStatus.OPEN

    def discharge(self, notes: str, now: datetime | None = None) -> None:
        if not self.is_open:
            raise HospitalizationAlreadyDischarged(self.id or 0)
        self.status = HospitalizationStatus.DISCHARGED
        self.discharge_notes = _trim(notes, "notas de alta", MAX_DISCHARGE_NOTES_LENGTH)
        self.discharged_at = now or datetime.now(UTC)


@dataclass(slots=True)
class HospitalizationNote:
    """Una nota de seguimiento diario. Solo la carga un veterinario."""

    hospitalization_id: int
    author_id: int
    note: str
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.note = _require_text(self.note, "nota", MAX_NOTE_LENGTH)


def _require_text(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if not value:
        raise InvalidHospitalization(f"El campo {field_name!r} es obligatorio.")
    if len(value) > max_length:
        raise InvalidHospitalization(
            f"El campo {field_name!r} admite {max_length} caracteres como máximo."
        )
    return value


def _trim(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if len(value) > max_length:
        raise InvalidHospitalization(
            f"El campo {field_name!r} admite {max_length} caracteres como máximo."
        )
    return value

"""Entidades de dominio de la historia clínica.

Python puro. La mascota y el veterinario se referencian por identificador:
cada uno vive en otro módulo y este no puede importarlos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from gestvet.modules.medical_records.domain.exceptions import InvalidClinicalEntry

MAX_NOTES_LENGTH = 2000
MAX_DIAGNOSIS_LENGTH = 300
MAX_TREATMENT_LENGTH = 300

# Ningún animal doméstico pesa esto. Un valor mayor no es una mascota grande,
# es un dato mal tipeado.
MAX_PLAUSIBLE_WEIGHT_KG = Decimal("120")


class EntryKind(StrEnum):
    CONSULTATION = "consultation"
    VACCINE = "vaccine"
    SURGERY = "surgery"
    FOLLOW_UP = "follow_up"
    CONSENT_FORM = "consent_form"
    OTHER = "other"

    @property
    def label(self) -> str:
        return _KIND_LABELS[self]


_KIND_LABELS: dict[EntryKind, str] = {
    EntryKind.CONSULTATION: "Consulta",
    EntryKind.VACCINE: "Vacuna",
    EntryKind.SURGERY: "Cirugía",
    EntryKind.FOLLOW_UP: "Control",
    EntryKind.CONSENT_FORM: "Carta de consentimiento",
    EntryKind.OTHER: "Otro",
}


@dataclass(slots=True)
class ClinicalEntry:
    pet_id: int
    veterinarian_id: int
    kind: EntryKind
    notes: str
    diagnosis: str = ""
    treatment: str = ""
    weight_kg: Decimal | None = None
    appointment_id: int | None = None
    id: int | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.notes = _require_text(self.notes, "notas", MAX_NOTES_LENGTH)
        self.diagnosis = _trim(self.diagnosis, "diagnóstico", MAX_DIAGNOSIS_LENGTH)
        self.treatment = _trim(self.treatment, "tratamiento", MAX_TREATMENT_LENGTH)
        if self.weight_kg is not None:
            _require_plausible_weight(self.weight_kg)
        if self.occurred_at.tzinfo is None:
            raise InvalidClinicalEntry("La fecha de la entrada debe traer zona horaria.")
        self.occurred_at = self.occurred_at.astimezone(UTC)


def _require_text(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if not value:
        raise InvalidClinicalEntry(f"El campo {field_name!r} es obligatorio.")
    if len(value) > max_length:
        raise InvalidClinicalEntry(
            f"El campo {field_name!r} admite {max_length} caracteres como máximo."
        )
    return value


def _trim(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if len(value) > max_length:
        raise InvalidClinicalEntry(
            f"El campo {field_name!r} admite {max_length} caracteres como máximo."
        )
    return value


def _require_plausible_weight(weight_kg: Decimal) -> None:
    if weight_kg <= 0:
        raise InvalidClinicalEntry("El peso debe ser positivo.")
    if weight_kg > MAX_PLAUSIBLE_WEIGHT_KG:
        raise InvalidClinicalEntry(
            f"El peso supera los {MAX_PLAUSIBLE_WEIGHT_KG} kg. Revisa el dato."
        )

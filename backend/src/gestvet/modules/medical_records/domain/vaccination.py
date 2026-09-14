"""Carnet de vacunas.

Una vacuna no es una nota más de la historia clínica: tiene fecha de aplicación,
producto, lote y, sobre todo, una próxima dosis. Con eso el dueño sabe si su
mascota está al día y el veterinario ve qué falta antes de empezar la consulta.

El catálogo sigue el esquema habitual en Perú: la antirrábica es obligatoria y
anual para perros y gatos; la séxtuple u óctuple en perros y la triple felina en
gatos se ponen en serie mientras la mascota es cachorra y después se refuerzan
cada año. El veterinario siempre puede cambiar la fecha sugerida.

Python puro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum

from gestvet.core.clinic_time import clinic_date
from gestvet.modules.medical_records.domain.exceptions import InvalidVaccination

MAX_PRODUCT_LENGTH = 80
MAX_BATCH_LENGTH = 40
MAX_VACCINATION_NOTES_LENGTH = 300

# Cuánto antes del vencimiento se avisa que una vacuna "vence pronto".
DUE_SOON_DAYS = 30
# Mientras es cachorra, las dosis de la serie inicial van cada tres semanas.
PRIMARY_SERIES_DAYS = 21
ADULT_AGE_DAYS = 365
YEARLY_DAYS = 365
DEWORMING_DAYS = 90

DOG = "Perro"
CAT = "Gato"


class VaccineCode(StrEnum):
    RABIES = "rabies"
    DOG_MULTIVALENT = "dog_multivalent"
    DOG_KENNEL_COUGH = "dog_kennel_cough"
    CAT_TRIPLE = "cat_triple"
    CAT_LEUKEMIA = "cat_leukemia"
    DEWORMING = "deworming"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class VaccineInfo:
    label: str
    # Sin especies, sirve para cualquiera.
    species: frozenset[str]
    booster_days: int | None
    primary_series: bool = False

    def applies_to(self, species: str) -> bool:
        return not self.species or species in self.species


VACCINES: dict[VaccineCode, VaccineInfo] = {
    VaccineCode.RABIES: VaccineInfo("Antirrábica", frozenset({DOG, CAT}), YEARLY_DAYS),
    VaccineCode.DOG_MULTIVALENT: VaccineInfo(
        "Séxtuple u óctuple (moquillo, parvovirus y otras)",
        frozenset({DOG}),
        YEARLY_DAYS,
        primary_series=True,
    ),
    VaccineCode.DOG_KENNEL_COUGH: VaccineInfo(
        "Tos de las perreras (Bordetella)", frozenset({DOG}), YEARLY_DAYS
    ),
    VaccineCode.CAT_TRIPLE: VaccineInfo(
        "Triple felina", frozenset({CAT}), YEARLY_DAYS, primary_series=True
    ),
    VaccineCode.CAT_LEUKEMIA: VaccineInfo("Leucemia felina", frozenset({CAT}), YEARLY_DAYS),
    VaccineCode.DEWORMING: VaccineInfo("Desparasitación", frozenset(), DEWORMING_DAYS),
    VaccineCode.OTHER: VaccineInfo("Otra vacuna", frozenset(), None),
}


def vaccines_for(species: str) -> list[tuple[VaccineCode, VaccineInfo]]:
    """Las vacunas que tienen sentido para una especie, en el orden del catálogo."""
    return [(code, info) for code, info in VACCINES.items() if info.applies_to(species)]


def suggested_interval_days(
    code: VaccineCode, *, applied_on: date, birth_date: date | None
) -> int | None:
    """Cuántos días hasta la próxima dosis, o `None` si no lleva refuerzo."""
    info = VACCINES[code]
    if info.booster_days is None:
        return None
    is_young = birth_date is not None and (applied_on - birth_date).days < ADULT_AGE_DAYS
    return PRIMARY_SERIES_DAYS if info.primary_series and is_young else info.booster_days


class VaccinationStatus(StrEnum):
    OVERDUE = "overdue"
    DUE_SOON = "due_soon"
    UP_TO_DATE = "up_to_date"
    NO_BOOSTER = "no_booster"

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]


_STATUS_LABELS: dict[VaccinationStatus, str] = {
    VaccinationStatus.OVERDUE: "Vencida",
    VaccinationStatus.DUE_SOON: "Vence pronto",
    VaccinationStatus.UP_TO_DATE: "Al día",
    VaccinationStatus.NO_BOOSTER: "Sin refuerzo",
}

# Lo más urgente primero en el carnet.
_URGENCY = list(VaccinationStatus)


def status_on(next_due_on: date | None, today: date) -> VaccinationStatus:
    if next_due_on is None:
        return VaccinationStatus.NO_BOOSTER
    if next_due_on < today:
        return VaccinationStatus.OVERDUE
    if (next_due_on - today).days <= DUE_SOON_DAYS:
        return VaccinationStatus.DUE_SOON
    return VaccinationStatus.UP_TO_DATE


def _trim(raw: str, label: str, max_length: int) -> str:
    value = raw.strip()
    if len(value) > max_length:
        raise InvalidVaccination(f"El campo {label!r} admite {max_length} caracteres como máximo.")
    return value


@dataclass(slots=True)
class Vaccination:
    pet_id: int
    veterinarian_id: int
    vaccine: VaccineCode
    applied_on: date
    next_due_on: date | None = None
    product_name: str = ""
    batch: str = ""
    notes: str = ""
    appointment_id: int | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.product_name = _trim(self.product_name, "producto", MAX_PRODUCT_LENGTH)
        self.batch = _trim(self.batch, "lote", MAX_BATCH_LENGTH)
        self.notes = _trim(self.notes, "notas", MAX_VACCINATION_NOTES_LENGTH)
        if self.id is None and self.applied_on > clinic_date(datetime.now(UTC)):
            raise InvalidVaccination("La fecha de aplicación no puede estar en el futuro.")
        if self.next_due_on is not None and self.next_due_on <= self.applied_on:
            raise InvalidVaccination("La próxima dosis tiene que ser después de la aplicación.")
        if self.vaccine is VaccineCode.OTHER and not self.product_name:
            raise InvalidVaccination("Para otra vacuna, escribe el nombre del producto.")

    @property
    def label(self) -> str:
        if self.vaccine is VaccineCode.OTHER:
            return self.product_name
        return VACCINES[self.vaccine].label


@dataclass(frozen=True, slots=True)
class VaccineStatusSummary:
    vaccine: VaccineCode
    label: str
    last_applied_on: date
    next_due_on: date | None
    status: VaccinationStatus


def summarize(vaccinations: list[Vaccination], today: date) -> list[VaccineStatusSummary]:
    """El estado de cada vacuna según su última aplicación, lo más urgente primero.

    "Otra vacuna" se agrupa por producto: dos vacunas distintas cargadas como
    "otra" no pueden pisarse entre sí.
    """
    latest: dict[tuple[VaccineCode, str], Vaccination] = {}
    for item in sorted(vaccinations, key=lambda v: (v.applied_on, v.id or 0)):
        key = (item.vaccine, item.label.casefold() if item.vaccine is VaccineCode.OTHER else "")
        latest[key] = item
    summaries = [
        VaccineStatusSummary(
            vaccine=item.vaccine,
            label=item.label,
            last_applied_on=item.applied_on,
            next_due_on=item.next_due_on,
            status=status_on(item.next_due_on, today),
        )
        for item in latest.values()
    ]
    return sorted(summaries, key=lambda s: (_URGENCY.index(s.status), s.next_due_on or date.max))

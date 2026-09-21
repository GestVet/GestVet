"""Especialidades veterinarias.

Cada veterinario declara con qué se preparó para atender: una disciplina
(cardiología, cirugía...), un tipo de animal (exóticos, equinos...) o un cargo
fuera de la clínica (salud pública, investigación...). El catálogo es cerrado
para que "cardiologia", "Cardiología" y "cardio" no sean tres especialidades
distintas, y lo amplía la administración cuando hace falta una que no está.

Elegir con qué especialidad reservar es responsabilidad de quien reserva: el
catálogo solo ofrece las opciones, no valida que la dolencia descrita
corresponda a la especialidad elegida.

Python puro.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from gestvet.modules.accounts.domain.exceptions import InvalidSpecialty

MAX_NAME_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 240
_MIN_NAME_LENGTH = 3


class SpecialtyCategory(StrEnum):
    DISCIPLINE = "discipline"
    ANIMAL_TYPE = "animal_type"
    INDUSTRY = "industry"

    @property
    def label(self) -> str:
        return _CATEGORY_LABELS[self]


_CATEGORY_LABELS: dict[SpecialtyCategory, str] = {
    SpecialtyCategory.DISCIPLINE: "Por disciplina",
    SpecialtyCategory.ANIMAL_TYPE: "Por tipo de animal",
    SpecialtyCategory.INDUSTRY: "Cargos e investigación",
}

# El orden en que la pantalla de reserva y la de administración muestran las
# categorías.
CATEGORY_ORDER: tuple[SpecialtyCategory, ...] = (
    SpecialtyCategory.DISCIPLINE,
    SpecialtyCategory.ANIMAL_TYPE,
    SpecialtyCategory.INDUSTRY,
)


def specialty_key(name: str) -> str:
    """La forma de comparar nombres: sin tildes, sin mayúsculas y sin espacios de más."""
    sin_tildes = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.casefold().split())


def format_specialty_name(raw: str) -> str:
    text = " ".join(raw.split())
    if len(text) < _MIN_NAME_LENGTH:
        raise InvalidSpecialty("Escribe el nombre de la especialidad, con al menos tres letras.")
    if len(text) > MAX_NAME_LENGTH:
        raise InvalidSpecialty(
            f"El nombre de la especialidad admite hasta {MAX_NAME_LENGTH} caracteres."
        )
    return text


def _validated_description(raw: str) -> str:
    description = raw.strip()
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise InvalidSpecialty(f"La descripción admite hasta {MAX_DESCRIPTION_LENGTH} caracteres.")
    return description


@dataclass(slots=True)
class Specialty:
    name: str
    category: SpecialtyCategory
    description: str = ""
    is_active: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = format_specialty_name(self.name)
        self.description = _validated_description(self.description)

    def update(
        self, *, name: str, category: SpecialtyCategory, description: str, is_active: bool
    ) -> None:
        self.name = format_specialty_name(name)
        self.category = category
        self.description = _validated_description(description)
        self.is_active = is_active

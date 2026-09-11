"""Entidades de dominio de mascotas.

Python puro. Sin FastAPI, sin SQLAlchemy, sin Pydantic, y los contratos de
Import Linter lo verifican.

El dueño se referencia por identificador y no por entidad. `accounts` es otro
módulo y este no puede importarlo: quien necesite el nombre del dueño lo pide
al módulo que lo posee.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from gestvet.pets.domain.exceptions import InvalidPetData

MAX_NAME_LENGTH = 60
MAX_SPECIES_LENGTH = 40
MAX_BREED_LENGTH = 60

# Ninguna especie domestica se acerca a esto. Un valor mayor no es una mascota
# longeva, es una fecha mal tipeada.
MAX_PLAUSIBLE_AGE_YEARS = 60


@dataclass(slots=True)
class Pet:
    name: str
    species: str
    breed: str
    birth_date: date
    owner_id: int
    is_active: bool = True
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.name = _require_text(self.name, "nombre", MAX_NAME_LENGTH)
        self.species = _require_text(self.species, "especie", MAX_SPECIES_LENGTH)
        self.breed = _require_text(self.breed, "raza", MAX_BREED_LENGTH)
        _require_plausible_birth_date(self.birth_date)

    def age_in_years(self, today: date | None = None) -> int:
        """Edad cumplida.

        El original guardaba la edad como un número, que envejece mal: queda
        congelada el día que se escribe. Se guarda la fecha y la edad se
        calcula, que es la misma informacion sin el defecto.
        """
        reference = today or datetime.now(UTC).date()
        years = reference.year - self.birth_date.year
        if (reference.month, reference.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return max(years, 0)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def belongs_to(self, owner_id: int) -> bool:
        return self.owner_id == owner_id


def _require_text(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if not value:
        raise InvalidPetData(f"El campo {field_name!r} es obligatorio.")
    if len(value) > max_length:
        raise InvalidPetData(f"El campo {field_name!r} admite {max_length} caracteres como máximo.")
    return value


def _require_plausible_birth_date(birth_date: date, today: date | None = None) -> None:
    reference = today or datetime.now(UTC).date()
    if birth_date > reference:
        raise InvalidPetData("La fecha de nacimiento no puede estar en el futuro.")
    if reference.year - birth_date.year > MAX_PLAUSIBLE_AGE_YEARS:
        raise InvalidPetData(
            f"La fecha de nacimiento supera los {MAX_PLAUSIBLE_AGE_YEARS} años. "
            "Revisá el dato antes de guardarlo."
        )

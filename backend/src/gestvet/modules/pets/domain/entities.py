"""Entidades de dominio de mascotas.

Python puro. Sin FastAPI, sin SQLAlchemy, sin Pydantic, y los contratos de
Import Linter lo verifican.

El dueño se referencia por identificador y no por entidad. `accounts` es otro
módulo y este no puede importarlo: quien necesite el nombre del dueño lo pide
al módulo que lo posee.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

from gestvet.modules.pets.domain.exceptions import InvalidPetData

MAX_NAME_LENGTH = 60
MAX_SPECIES_LENGTH = 40
MAX_BREED_LENGTH = 60
MAX_COLOR_LENGTH = 80
MAX_MICROCHIP_LENGTH = 40
MAX_TEMPERAMENT_LENGTH = 120
MAX_ALLERGIES_LENGTH = 300
# Un microchip ISO tiene 15 dígitos; los más antiguos, 9 o 10.
_MICROCHIP_PATTERN = re.compile(r"\d{9,15}")

# Ninguna especie domestica se acerca a esto. Un valor mayor no es una mascota
# longeva, es una fecha mal tipeada.
MAX_PLAUSIBLE_AGE_YEARS = 60

# Cubre desde un hámster hasta un gran danés sin abrir la puerta a un dato mal
# tipeado. Un caballo o una vaca no son mascotas de esta clínica.
MAX_PLAUSIBLE_WEIGHT_KG = Decimal("120")
MAX_PLAUSIBLE_HEIGHT_CM = Decimal("200")


class PetSex(StrEnum):
    MALE = "male"
    FEMALE = "female"

    @property
    def label(self) -> str:
        return _SEX_LABELS[self]


_SEX_LABELS: dict[PetSex, str] = {
    PetSex.MALE: "Macho",
    PetSex.FEMALE: "Hembra",
}


@dataclass(slots=True)
class Pet:
    name: str
    species: str
    breed: str
    birth_date: date
    owner_id: int
    is_active: bool = True
    # Lo carga el dueño: lo conoce de memoria, no necesita medirlo.
    sex: PetSex | None = None
    color: str = ""
    microchip_number: str = ""
    temperament: str = ""
    # Lo carga el veterinario: son datos clínicos, medidos o confirmados en
    # consulta.
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    is_sterilized: bool | None = None
    allergies: str = ""
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.name = _require_text(self.name, "nombre", MAX_NAME_LENGTH)
        self.species = _require_text(self.species, "especie", MAX_SPECIES_LENGTH)
        self.breed = _require_text(self.breed, "raza", MAX_BREED_LENGTH)
        _require_plausible_birth_date(self.birth_date)
        self.color = _trim(self.color, "color", MAX_COLOR_LENGTH)
        self.microchip_number = _trim(self.microchip_number, "microchip", MAX_MICROCHIP_LENGTH)
        self.temperament = _trim(self.temperament, "temperamento", MAX_TEMPERAMENT_LENGTH)
        self.allergies = _trim(self.allergies, "alergias", MAX_ALLERGIES_LENGTH)
        if self.weight_kg is not None:
            _require_plausible_weight(self.weight_kg)
        if self.height_cm is not None:
            _require_plausible_height(self.height_cm)

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

    def update_owner_profile(
        self,
        *,
        sex: PetSex | None,
        color: str,
        microchip_number: str,
        temperament: str,
        species: str | None = None,
        breed: str | None = None,
        birth_date: date | None = None,
    ) -> None:
        """Datos que conoce el dueño, no el consultorio.

        Especie, raza y fecha de nacimiento son opcionales: sin ellas se
        conservan. Sirven para completar una mascota dada de alta en una
        emergencia, que queda con la raza sin especificar.
        """
        # Se valida todo antes de tocar nada: un dato inválido no deja la ficha
        # a medio actualizar.
        nuevo_color = _trim(color, "color", MAX_COLOR_LENGTH)
        nuevo_microchip = _require_microchip(microchip_number)
        nuevo_temperamento = _trim(temperament, "temperamento", MAX_TEMPERAMENT_LENGTH)
        nueva_especie = (
            self.species
            if species is None
            else _require_text(species, "especie", MAX_SPECIES_LENGTH)
        )
        nueva_raza = self.breed if breed is None else _require_text(breed, "raza", MAX_BREED_LENGTH)
        if birth_date is not None:
            _require_plausible_birth_date(birth_date)
            self.birth_date = birth_date
        self.species = nueva_especie
        self.breed = nueva_raza
        self.sex = sex
        self.color = nuevo_color
        self.microchip_number = nuevo_microchip
        self.temperament = nuevo_temperamento

    def update_clinical_profile(
        self,
        *,
        weight_kg: Decimal | None,
        height_cm: Decimal | None,
        is_sterilized: bool | None,
        allergies: str,
    ) -> None:
        """Datos que se miden o se confirman en consulta."""
        if weight_kg is not None:
            _require_plausible_weight(weight_kg)
        if height_cm is not None:
            _require_plausible_height(height_cm)
        self.weight_kg = weight_kg
        self.height_cm = height_cm
        self.is_sterilized = is_sterilized
        self.allergies = _trim(allergies, "alergias", MAX_ALLERGIES_LENGTH)


def _require_text(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if not value:
        raise InvalidPetData(f"El campo {field_name!r} es obligatorio.")
    if len(value) > max_length:
        raise InvalidPetData(f"El campo {field_name!r} admite {max_length} caracteres como máximo.")
    return value


def _trim(raw: str, field_name: str, max_length: int) -> str:
    value = raw.strip()
    if len(value) > max_length:
        raise InvalidPetData(f"El campo {field_name!r} admite {max_length} caracteres como máximo.")
    return value


def _require_microchip(raw: str) -> str:
    value = _trim(raw, "microchip", MAX_MICROCHIP_LENGTH)
    if value and not _MICROCHIP_PATTERN.fullmatch(value):
        raise InvalidPetData("El microchip tiene de 9 a 15 dígitos, sin espacios ni letras.")
    return value


def _require_plausible_birth_date(birth_date: date, today: date | None = None) -> None:
    reference = today or datetime.now(UTC).date()
    if birth_date > reference:
        raise InvalidPetData("La fecha de nacimiento no puede estar en el futuro.")
    if reference.year - birth_date.year > MAX_PLAUSIBLE_AGE_YEARS:
        raise InvalidPetData(
            f"La fecha de nacimiento supera los {MAX_PLAUSIBLE_AGE_YEARS} años. "
            "Revisa el dato antes de guardarlo."
        )


def _require_plausible_weight(weight_kg: Decimal) -> None:
    if weight_kg <= 0:
        raise InvalidPetData("El peso debe ser positivo.")
    if weight_kg > MAX_PLAUSIBLE_WEIGHT_KG:
        raise InvalidPetData(f"El peso supera los {MAX_PLAUSIBLE_WEIGHT_KG} kg. Revisa el dato.")


def _require_plausible_height(height_cm: Decimal) -> None:
    if height_cm <= 0:
        raise InvalidPetData("La altura debe ser positiva.")
    if height_cm > MAX_PLAUSIBLE_HEIGHT_CM:
        raise InvalidPetData(f"La altura supera los {MAX_PLAUSIBLE_HEIGHT_CM} cm. Revisa el dato.")

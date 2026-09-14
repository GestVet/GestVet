"""Catálogo de especies y razas.

Una lista cerrada en vez de texto libre: "perro", "Perro", "can" y "perrito"
eran cuatro especies distintas para cualquier búsqueda o indicador. La lista
vive en la base: la siembra una migración y la administración la amplía cuando
llega un animal que no está, sin esperar un despliegue.

Todo nombre nuevo pasa por `format_catalog_name`, así el catálogo entero tiene
una sola forma de escribirse sin importar cómo lo tipee quien lo carga. Dos
nombres que solo difieren en tildes, mayúsculas o espacios son el mismo:
`catalog_key` los iguala para no dejar entrar duplicados.

Nada se borra: una especie o raza en desuso se desactiva. Las mascotas guardan
el nombre, y borrarlo dejaría fichas apuntando a algo que ya no existe.

Python puro.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from gestvet.modules.pets.domain.entities import MAX_BREED_LENGTH, MAX_SPECIES_LENGTH
from gestvet.modules.pets.domain.exceptions import CatalogEntryLocked, InvalidPetData

UNKNOWN_BREED = "Sin especificar"
MIXED_BREED = "Mestizo"
OTHER_BREED = "Otra raza"

# Las especies de la siembra van primero, en el orden en que son comunes; las
# que agrega la administración, después y por nombre. "Otro" se siembra con un
# orden mayor, así queda siempre al final.
ADDED_SPECIES_ORDER = 500

_MIN_NAME_LENGTH = 2
_ALLOWED_SYMBOLS = frozenset(" '-().")
# Palabras que van en minúscula en medio de un nombre: "Perro sin pelo del Perú".
_CONNECTORS = frozenset(
    {"a", "al", "con", "de", "del", "e", "el", "en", "la", "las", "los", "o", "sin", "u", "y"}
)


def catalog_key(name: str) -> str:
    """La forma de comparar nombres: sin tildes, sin mayúsculas y sin espacios de más."""
    sin_tildes = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.casefold().split())


def _letters(word: str) -> str:
    return "".join(character for character in word if character.isalpha())


def _is_capitalized(word: str) -> bool:
    letters = _letters(word)
    return letters[:1].isupper() and letters[1:] == letters[1:].lower()


def _upper_first_letter(word: str) -> str:
    for index, character in enumerate(word):
        if character.isalpha():
            return word[:index] + character.upper() + word[index + 1 :]
    return word


def _require_valid_text(text: str, label: str, max_length: int) -> None:
    if len(_letters(text)) < _MIN_NAME_LENGTH:
        raise InvalidPetData(f"Escribe el nombre de la {label}, con al menos dos letras.")
    if len(text) > max_length:
        raise InvalidPetData(f"El nombre de la {label} admite hasta {max_length} caracteres.")
    if any(not (char.isalpha() or char in _ALLOWED_SYMBOLS) for char in text):
        raise InvalidPetData(
            f"El nombre de la {label} solo lleva letras, espacios, guiones, "
            "apóstrofos, puntos y paréntesis."
        )


def format_catalog_name(raw: str, label: str, max_length: int) -> str:
    """Deja un nombre con la forma única del catálogo.

    Mayúscula solo al inicio y el resto en minúscula: "PASTOR ALEMÁN",
    "pastor alemán" y "Pastor Alemán" quedan "Pastor alemán". Un nombre propio
    conserva su mayúscula si quien escribe deja otra palabra en minúscula, que
    es la señal de que eligió a propósito dónde va cada mayúscula: "perro sin
    pelo del Perú" queda "Perro sin pelo del Perú".
    """
    words = raw.split()
    text = " ".join(words)
    _require_valid_text(text, label, max_length)

    deliberate = any(word == word.lower() and _letters(word) for word in words[1:])
    formatted = [_upper_first_letter(words[0].lower())]
    for word in words[1:]:
        keeps_capital = deliberate and word.lower() not in _CONNECTORS and _is_capitalized(word)
        formatted.append(word if keeps_capital else word.lower())
    return " ".join(formatted)


def format_species_name(raw: str) -> str:
    return format_catalog_name(raw, "especie", MAX_SPECIES_LENGTH)


def format_breed_name(raw: str) -> str:
    return format_catalog_name(raw, "raza", MAX_BREED_LENGTH)


def breed_sort_key(name: str) -> tuple[int, str]:
    """Primero «Sin especificar» y «Mestizo», para encontrarlos rápido; «Otra raza», al final."""
    fixed = {UNKNOWN_BREED: 0, MIXED_BREED: 1, OTHER_BREED: 3}
    return (fixed.get(name, 2), catalog_key(name))


@dataclass(slots=True)
class Breed:
    name: str
    species_id: int
    is_active: bool = True
    id: int | None = None

    @property
    def is_locked(self) -> bool:
        # Las altas de emergencia la usan cuando nadie sabe la raza: sin ella,
        # no se podría registrar a la mascota de esa especie.
        return self.name == UNKNOWN_BREED

    def update(self, *, name: str, is_active: bool) -> None:
        if self.is_locked and (name != self.name or not is_active):
            raise CatalogEntryLocked(
                f"«{UNKNOWN_BREED}» se usa en las altas de emergencia: no se renombra "
                "ni se desactiva."
            )
        self.name = name
        self.is_active = is_active


@dataclass(slots=True)
class Species:
    name: str
    is_active: bool = True
    sort_order: int = ADDED_SPECIES_ORDER
    id: int | None = None
    breeds: list[Breed] = field(default_factory=list)

    def update(self, *, name: str, is_active: bool) -> None:
        self.name = name
        self.is_active = is_active

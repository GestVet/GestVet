"""Catálogo de especies y razas.

Una lista cerrada en vez de texto libre: "perro", "Perro", "can" y "perrito"
eran cuatro especies distintas para cualquier búsqueda o indicador. Refleja las
mascotas de los hogares peruanos (INEI 2025: perros 52 %, gatos 33 % y el resto
aves, conejos, cuyes, tortugas y peces) e incluye al perro sin pelo del Perú.

Cada especie acepta "Sin especificar": en una emergencia nadie tiene tiempo de
averiguar la raza, y es más honesto que inventarla. Python puro.
"""

from __future__ import annotations

from gestvet.modules.pets.domain.exceptions import InvalidPetData

UNKNOWN_BREED = "Sin especificar"
MIXED_BREED = "Mestizo"
OTHER_BREED = "Otra raza"

_CATALOG: dict[str, tuple[str, ...]] = {
    "Perro": (
        MIXED_BREED,
        "Perro sin pelo del Perú",
        "Beagle",
        "Border collie",
        "Boxer",
        "Bulldog francés",
        "Bulldog inglés",
        "Chihuahua",
        "Cocker spaniel",
        "Dálmata",
        "Dóberman",
        "Golden retriever",
        "Husky siberiano",
        "Labrador retriever",
        "Maltés",
        "Pastor alemán",
        "Pequinés",
        "Pitbull",
        "Pomerania",
        "Poodle",
        "Pug",
        "Rottweiler",
        "Schnauzer",
        "Shar pei",
        "Shih tzu",
        "Yorkshire terrier",
        OTHER_BREED,
    ),
    "Gato": (
        MIXED_BREED,
        "Angora",
        "Bengalí",
        "British shorthair",
        "Maine coon",
        "Persa",
        "Ragdoll",
        "Siamés",
        "Sphynx",
        OTHER_BREED,
    ),
    "Ave": ("Agapornis", "Cacatúa", "Canario", "Loro", "Periquito australiano", OTHER_BREED),
    "Conejo": (MIXED_BREED, "Belier", "Cabeza de león", "Enano holandés", "Rex", OTHER_BREED),
    "Roedor": ("Chinchilla", "Cuy", "Hámster", "Jerbo", "Rata", "Ratón", OTHER_BREED),
    "Reptil": (
        "Dragón barbudo",
        "Gecko leopardo",
        "Iguana",
        "Serpiente",
        "Tortuga acuática",
        "Tortuga terrestre",
        OTHER_BREED,
    ),
    "Pez": ("Betta", "Goldfish", "Guppy", OTHER_BREED),
    "Otro": (),
}

SPECIES_CATALOG: dict[str, tuple[str, ...]] = {
    species: (*breeds, UNKNOWN_BREED) for species, breeds in _CATALOG.items()
}


def ensure_in_catalog(species: str, breed: str) -> None:
    """La especie es de la lista y la raza, de las de esa especie."""
    breeds = SPECIES_CATALOG.get(species.strip())
    if breeds is None:
        raise InvalidPetData("Elige una especie de la lista.")
    if breed.strip() not in breeds:
        raise InvalidPetData(f"Elige una raza de la lista para {species.strip()}.")

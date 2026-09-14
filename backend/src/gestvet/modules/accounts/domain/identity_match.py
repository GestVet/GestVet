"""Si el nombre que escribió una persona corresponde al de su DNI.

No se exige una copia exacta: la gente escribe "María" o "maria", un solo
nombre de los dos o solo el primer apellido. Alcanza con que el primer nombre
escrito esté entre los nombres del DNI y el primer apellido escrito sea parte
del apellido paterno ("de la Cruz" cuenta para "DE LA CRUZ").

Python puro.
"""

from __future__ import annotations

import unicodedata

from gestvet.core.identity_registry import PersonName


def _words(text: str) -> list[str]:
    without_accents = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()
    return [word for word in without_accents.casefold().replace("-", " ").split() if word]


def names_match(first_name: str, last_name: str, registered: PersonName) -> bool:
    given = _words(first_name)
    surnames = _words(last_name)
    if not given or not surnames:
        return False
    return given[0] in _words(registered.first_names) and surnames[0] in _words(
        registered.paternal_surname
    )

"""Errores de dominio de mascotas.

Los adaptadores los traducen a códigos HTTP. El dominio no conoce HTTP.
"""

from __future__ import annotations


class PetsError(Exception):
    """Raíz de los errores del módulo de mascotas."""


class InvalidPetData(PetsError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class PetNotFound(PetsError):
    def __init__(self, pet_id: int) -> None:
        super().__init__(f"No existe la mascota {pet_id}.")
        self.pet_id = pet_id


class PetStatusIsFinal(PetsError):
    """Fallecida es un hecho, no un estado administrativo: no se revierte solo."""

    def __init__(self, pet_id: int) -> None:
        super().__init__(
            "La mascota ya fue registrada como fallecida. Si fue un error de carga, "
            "pedile al personal de la clínica que lo corrija."
        )
        self.pet_id = pet_id


class CatalogEntryNotFound(PetsError):
    def __init__(self, kind: str, entry_id: int) -> None:
        super().__init__(f"No existe la {kind} {entry_id}.")
        self.entry_id = entry_id


class CatalogNameTaken(PetsError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Ya existe «{name}» en el catálogo.")
        self.name = name


class CatalogEntryLocked(PetsError):
    """Una entrada del catálogo que el sistema necesita tal como está."""

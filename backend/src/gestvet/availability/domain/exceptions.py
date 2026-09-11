"""Errores de dominio de disponibilidad."""

from __future__ import annotations


class AvailabilityError(Exception):
    """Raíz de los errores del módulo de disponibilidad."""


class InvalidSlot(AvailabilityError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class OverlappingSlot(AvailabilityError):
    def __init__(self) -> None:
        super().__init__("El tramo se superpone con otro ya publicado.")


class SlotNotFound(AvailabilityError):
    def __init__(self, slot_id: int) -> None:
        super().__init__(f"No existe el tramo de disponibilidad {slot_id}.")
        self.slot_id = slot_id

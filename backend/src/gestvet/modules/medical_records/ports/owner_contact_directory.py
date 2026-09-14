"""Lector hacia `pets` y `accounts`: a quién avisarle de una vacuna.

Un recordatorio de vacuna va al dueño de la mascota, por WhatsApp. La relación
vive en `pets` y el nombre y el teléfono en `users`: tablas ajenas, que este
módulo lee y nunca escribe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OwnerContact:
    owner_name: str
    phone: str
    pet_name: str


class OwnerContactDirectory(Protocol):
    async def contact_for_pet(self, pet_id: int) -> OwnerContact | None:
        """`None` si la mascota está de baja o su dueño está desactivado."""
        ...

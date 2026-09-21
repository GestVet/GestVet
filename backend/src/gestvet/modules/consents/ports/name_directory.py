"""Lector de nombres para mostrar: la mascota y el veterinario de cada pedido.

El dueño tiene que ver sobre qué mascota y a pedido de quién firma. Los
nombres son de `pets` y de `accounts`; se leen de sus tablas y nunca se
escriben.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class NameDirectory(Protocol):
    async def pet_names(self, pet_ids: Iterable[int]) -> dict[int, str]: ...

    async def user_names(self, user_ids: Iterable[int]) -> dict[int, str]: ...

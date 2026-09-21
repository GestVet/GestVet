"""Puerto de persistencia para las preferencias de interfaz de usuario.

Define qué operaciones necesita el negocio para guardar, recuperar y
restablecer la disposición del sidebar y los bloques del panel principal.
"""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.accounts.domain.entities import UserLayoutPreference


class LayoutRepository(Protocol):
    async def get_by_user_id(self, user_id: int) -> UserLayoutPreference | None: ...

    async def save(self, preference: UserLayoutPreference) -> UserLayoutPreference: ...

    async def delete_by_user_id(self, user_id: int) -> None: ...

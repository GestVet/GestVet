"""Puerto de persistencia de los enlaces de recuperación de contraseña."""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.accounts.domain.entities import PasswordResetToken


class PasswordResetRepository(Protocol):
    async def add(self, token: PasswordResetToken) -> PasswordResetToken: ...

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None: ...

    async def save(self, token: PasswordResetToken) -> PasswordResetToken: ...

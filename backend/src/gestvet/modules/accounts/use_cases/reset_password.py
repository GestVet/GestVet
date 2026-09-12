"""Caso de uso: consumir un enlace de recuperación y fijar una contraseña nueva."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from gestvet.modules.accounts.domain.entities import hash_reset_token
from gestvet.modules.accounts.domain.exceptions import InvalidResetToken
from gestvet.modules.accounts.ports.password_reset_repository import PasswordResetRepository
from gestvet.modules.accounts.ports.user_repository import PasswordHasher, UserRepository


@dataclass(frozen=True, slots=True)
class ResetPasswordCommand:
    token: str
    new_password: str


class ResetPassword:
    def __init__(
        self,
        users: UserRepository,
        tokens: PasswordResetRepository,
        hasher: PasswordHasher,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._hasher = hasher

    async def __call__(self, command: ResetPasswordCommand) -> None:
        now = datetime.now(UTC)
        entry = await self._tokens.get_by_hash(hash_reset_token(command.token))
        if entry is None or not entry.is_valid(now):
            raise InvalidResetToken()

        user = await self._users.get(entry.user_id)
        if user is None:
            raise InvalidResetToken()

        user.password_hash = self._hasher.hash(command.new_password)
        await self._users.save(user)

        # Se marca usado recién cuando la contraseña ya quedó guardada: si el
        # guardado fallara, el enlace sigue sirviendo para reintentar.
        entry.mark_used(now)
        await self._tokens.save(entry)

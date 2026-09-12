"""Caso de uso: pedir un enlace de recuperación de contraseña.

No revela si el correo existe: la respuesta es la misma en los dos casos, y
la única diferencia observable es si llega un correo. Es la misma regla que
aplica el inicio de sesión.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from gestvet.modules.accounts.domain.entities import (
    RESET_TOKEN_TTL,
    PasswordResetToken,
    generate_reset_token,
    hash_reset_token,
    normalize_email,
)
from gestvet.modules.accounts.domain.exceptions import InvalidEmail
from gestvet.modules.accounts.ports.email_sender import EmailSender
from gestvet.modules.accounts.ports.password_reset_repository import PasswordResetRepository
from gestvet.modules.accounts.ports.user_repository import UserRepository


@dataclass(frozen=True, slots=True)
class RequestPasswordResetCommand:
    email: str


class RequestPasswordReset:
    def __init__(
        self,
        users: UserRepository,
        tokens: PasswordResetRepository,
        email_sender: EmailSender,
        frontend_base_url: str,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._email_sender = email_sender
        self._frontend_base_url = frontend_base_url

    async def __call__(self, command: RequestPasswordResetCommand) -> None:
        try:
            email = normalize_email(command.email)
        except InvalidEmail:
            return

        user = await self._users.get_by_email(email)
        if user is None or not user.is_active or user.id is None:
            return

        plain_token = generate_reset_token()
        entry = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_reset_token(plain_token),
            expires_at=datetime.now(UTC) + RESET_TOKEN_TTL,
        )
        await self._tokens.add(entry)

        reset_url = f"{self._frontend_base_url}/restablecer-contrasena?token={plain_token}"
        await self._email_sender.send_password_reset(to=user.email, reset_url=reset_url)

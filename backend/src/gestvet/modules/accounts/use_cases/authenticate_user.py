"""Caso de uso: intercambiar credenciales por un token de acceso."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.identity import AccessToken, TokenService
from gestvet.modules.accounts.domain.entities import User, normalize_email
from gestvet.modules.accounts.domain.exceptions import (
    AccountsError,
    InactiveAccount,
    InvalidCredentials,
    InvalidEmail,
)
from gestvet.modules.accounts.ports.user_repository import PasswordHasher, UserRepository


@dataclass(frozen=True, slots=True)
class AuthenticateUserCommand:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    user: User
    token: AccessToken


class AuthenticateUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    async def __call__(self, command: AuthenticateUserCommand) -> AuthenticatedSession:
        user = await self._find(command.email)

        # La verificación corre siempre, incluso sin usuario, para que un correo
        # inexistente tarde lo mismo que una contraseña equivocada.
        password_hash = user.password_hash if user else self._hasher.dummy_hash()
        password_matches = self._hasher.verify(command.password, password_hash)

        if user is None or not password_matches:
            raise InvalidCredentials()
        if not user.is_active:
            raise InactiveAccount(user.email)

        if user.id is None:
            # El repositorio incumplió su contrato: solo devuelve usuarios ya
            # persistidos, y esos siempre tienen identificador.
            raise AccountsError(f"La cuenta {user.email!r} llegó sin identificador.")

        return AuthenticatedSession(user=user, token=self._tokens.issue(user.id, user.role))

    async def _find(self, raw_email: str) -> User | None:
        try:
            email = normalize_email(raw_email)
        except InvalidEmail:
            # Un correo mal formado es una credencial equivocada, no un error
            # de validación: responder distinto revelaría el formato esperado.
            return None
        return await self._users.get_by_email(email)
